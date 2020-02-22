import copy
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from classdiff.tag_language import TagLanguage
from classdiff.config import Config


class Model(dict):
    _cached_file_names = None

    def find_scope(self, name, preferred_file):
        if self[preferred_file].has(name):
            return self[preferred_file].get_scope(name)
        for fname in self:
            if self[fname].has(name):
                return self[fname].get_scope(name)

    def get_file_by_scope(self, qualified_name):
        for fname in self:
            scope = self[fname].find_scope(qualified_name)
            if scope:
                return self[fname]

    def get_scope(self, qualified_name):
        for fname in self:
            scope = self[fname].find_scope(qualified_name)
            if scope:
                return scope

    def find_file(self, tag_ref, language):
        if tag_ref in self:
            return self[tag_ref]
        if not self._cached_file_names:
            self._cached_file_names = {f.split("/")[-1]: f
                                       for f in self.keys()}
        if tag_ref in self._cached_file_names:
            return self[self._cached_file_names[tag_ref]]

    def mark_changed_members(self):
        for fname in self:
            for scope in self[fname].get_scopes():
                for member in scope.get_members():
                    if self[fname].has_diff_touching(member.range):
                        if member.diffsym not in ("-", "+"):
                            member.diffsym = "~"


class File:
    def __init__(self, name=""):
        self.name = name
        self._scopes = {}
        self._diff_ranges = []
        self.package = name.rsplit("/", 1)[0] if "/" in name else ""

    def add_scope(self, scope):
        self._scopes[scope.name] = scope

    def add_tag(self, tag, diffsym=""):
        scope = None
        if self.has(tag.scope):
            scope = self._scopes[tag.scope]
        elif tag.scope == "-" or tag.scope == "":
            scope = self.get_global_scope()
        elif (Config.show_nested_classes or
              tag.language.only_works_with_nesting()):
            local_name = tag.language.local_name(tag.scope)
            if self.has(local_name):
                scope = self._scopes[local_name]
        if scope:
            scope.add_tag(tag, diffsym)

    def has(self, scope):
        return scope in self._scopes

    def get_scope(self, key):
        return self._scopes[key]

    def find_scope(self, qualified_name):
        for scope in self.get_scopes():
            if scope.qualified_name == qualified_name:
                return scope

    def get_scope_keys(self):
        return self._scopes.keys()

    def get_scopes(self):
        return self._scopes.values()

    def get_scope_count(self):
        return len(self._scopes)

    def get_global_scope(self):
        if not self.has(""):
            global_scope = Scope("", self.name)
            self.add_scope(global_scope)
        return self.get_scope("")

    def get_real_scopes(self):
        return [scope for scope in self.get_scopes()
                if not scope.is_global_scope()]

    def add_diff_range(self, r):
        self._diff_ranges.append(r)

    def has_diff_touching(self, other):
        for r in self._diff_ranges:
            if LineRange.touching(r, other):
                return True
        return False


class Scope:
    def __init__(self, name="", namespace="", diffsym="", stereotype=""):
        self._tags = {}
        self.name = name
        self.qualified_name = self._get_qualified_name(name, namespace)
        self.diffsym = diffsym
        self.stereotype = stereotype
        self.tagval_inherits = []
        self.rels = []
        self.range = None

    def _get_qualified_name(self, name, namespace):
        return namespace + (f":{name}" if name else "")

    def add_tag(self, tag, diffsym=""):
        key = tag.name + diffsym
        self._tags[key] = tag
        tag.diffsym = diffsym
        if self.is_global_scope():
            tag.is_static = False

    def is_interface(self):
        return self.stereotype == "interface"

    def add_inherit(self, other):
        self.tagval_inherits.append(other)

    def add_rel(self, other_qn, type, diffsym=""):
        if self.get_rel(other_qn):
            # Only allow one rel
            return
        self.rels.append(Rel(other_qn, type, diffsym))

    def get_rel_other_qns(self):
        return [rel.other_qn for rel in self.rels]

    def get_rel(self, other_qn):
        for rel in self.rels:
            if rel.other_qn == other_qn:
                return rel

    def get_tag(self, key):
        return self._tags[key]

    def get_tags_dict(self):
        return self._tags

    def get_attrs(self):
        return [t for t in self._tags.values() if isinstance(t, Attr)]

    def get_ops(self):
        return [t for t in self._tags.values() if isinstance(t, Op)]

    def get_invisible_tags(self):
        return [t for t in self._tags.values() if isinstance(t, InvisibleTag)]

    def get_tag_keys(self):
        return self._tags.keys()

    def get_members(self):
        return self.get_attrs() + self.get_ops()

    def is_empty(self):
        return not self.get_members()

    def is_global_scope(self):
        return self.name == ""

    def touches(self, range):
        if self.range and LineRange.touching(range, self.range):
            return True
        for tag in self.get_members():
            if LineRange.touching(range, tag.range):
                return True
        return False


class RelType(IntEnum):
    DERIV = 1
    REAL = 2
    ASSOC = 3


class Rel:
    def __init__(self, other_qn, type, diffsym=""):
        self.other_qn = other_qn
        self.type = type
        self.diffsym = diffsym


@dataclass
class Tag():
    fname: str
    kind: str
    roles: str
    name: str
    typeref: str
    scope: str
    visibility: str
    diffsym: str
    range

    def __init__(self):
        pass


@dataclass
class Attr(Tag):
    def __init__(self):
        super().__init__()


@dataclass
class Op(Tag):
    def __init__(self):
        super().__init__()


@dataclass
class InvisibleTag(Tag):
    def __init__(self):
        super().__init__()


class ModelFactory:
    def fromfile(self, tagpath):
        model = Model()

        if os.path.isdir(tagpath):
            tagpath = os.path.join(tagpath, "tags")
        if not os.path.isfile(tagpath):
            print("error:file not found: " + tagpath, file=sys.stderr)
            exit(1)
        with open(tagpath) as tagfile:
            for line in tagfile:
                if line.startswith("!_"):
                    continue
                cols = line.rstrip("\n").split("\t")
                fname = cols[0]
                roles = cols[1]
                kind = cols[2]
                access = cols[6]
                implementation = cols[7]
                language = TagLanguage(cols[9])
                name = language.name(cols[3])
                scope = language.scope(cols[5])
                if language.is_blacklisted():
                    continue
                if fname not in model:
                    model[fname] = File(fname)
                if language.is_scope(kind, roles, access, name):
                    stereotype = language.get_scope_stereotype(kind,
                                                               implementation)
                    t = Scope(name, fname, stereotype=stereotype)
                    inherits = cols[8]
                    if inherits != "" and inherits != "-":
                        for i in language.split_inherits(inherits):
                            t.add_inherit(i)
                    if not Config.show_nested_classes \
                            and language.is_nested(scope) \
                            and not language.only_works_with_nesting():
                        continue
                elif language.is_attr(kind, roles, access, name):
                    t = Attr()
                elif language.is_op(kind, roles, access, name):
                    t = Op()
                elif language.is_inv_tag(kind, roles, access, name):
                    t = InvisibleTag()
                else:
                    continue
                t.fname = fname
                t.roles = roles
                t.kind = kind
                t.name = name
                t.typeref = language.typeref(cols[4])
                t.scope = scope
                t.visibility = language.visibility(access)
                t.language = language
                t.is_static = language.is_static_member(kind, implementation)
                start_line = int(cols[10]) if cols[10].isdigit() else None
                end_line = int(cols[11]) if cols[11].isdigit() else None
                t.range = LineRange(start_line, end_line)

                if isinstance(t, Scope):
                    model[fname].add_scope(t)
                else:
                    model[fname].add_tag(t)

        self.complete_relationships_inheritance(model)
        self.complete_relationships_assoc(model)
        return model

    def complete_relationships_inheritance(self, model):
        for fname in model:
            for scope in model[fname].get_scopes():
                for inherit in scope.tagval_inherits:
                    other_scope = model.find_scope(inherit, fname)
                    if not other_scope:
                        # Ignore scopes we don't know
                        continue
                    if other_scope.is_interface():
                        reltype = RelType.REAL
                    else:
                        reltype = RelType.DERIV
                    scope.add_rel(other_scope.qualified_name, reltype)

    def complete_relationships_assoc(self, model):
        for fname in model:
            file = model[fname]
            for scope in file.get_scopes():
                for key in scope.get_tags_dict():
                    tag = scope.get_tag(key)
                    if tag.roles == "def":
                        continue
                    found_file = model.find_file(tag.name, tag.language)
                    if found_file:
                        other_scope = found_file.get_global_scope()
                    else:
                        # Also look for references to scopes
                        local_name = tag.language.local_name(tag.name)
                        other_scope = model.find_scope(local_name, fname)
                    if other_scope:
                        other_file = model.get_file_by_scope(
                            other_scope.qualified_name)
                        start_scope = self.pick_rel_scope(file, scope,
                                                          tag.range)
                        other_scope = self.pick_rel_scope(other_file,
                                                          other_scope)
                        if other_scope == start_scope:
                            # Ignore self-reference
                            continue
                        if (start_scope.is_global_scope() and
                                file.find_scope(other_scope.qualified_name)):
                            # Ignore reference from a file to its own scopes
                            continue
                        start_scope.add_rel(other_scope.qualified_name,
                                            RelType.ASSOC)

    def pick_rel_scope(self, file, scope, line_range=None):
        if (scope.is_global_scope() and scope.is_empty()
                and file.get_scope_count() == 2):
            return file.get_real_scopes()[0]
        if (Config.find_rel_scope_using_line_numbers
                and scope.is_global_scope()
                and line_range):
            for s in file.get_scopes():
                if s.touches(line_range):
                    return s
        return scope

    def diff(self, model_a, model_b):
        model = Model()
        fnames = self._merge_in_order(list(model_a.keys()),
                                      list(model_b.keys()))
        for fname in fnames:
            model[fname] = File(fname)
            file_a = model_a[fname] if fname in model_a else File()
            file_b = model_b[fname] if fname in model_b else File()
            snames = self._merge_in_order(list(file_a.get_scope_keys()),
                                          list(file_b.get_scope_keys()))
            for sname in snames:
                scope_a = (file_a.get_scope(sname) if file_a.has(sname) else
                           Scope())
                scope_b = (file_b.get_scope(sname) if file_b.has(sname) else
                           Scope())
                tnames = self._merge_in_order(list(scope_a.get_tag_keys()),
                                              list(scope_b.get_tag_keys()))
                sdiffsym = (" " if file_a.has(sname) and file_b.has(sname) else
                            "-" if file_a.has(sname) else
                            "+")
                stereotype = scope_b.stereotype or scope_a.stereotype
                scope = Scope(sname, fname, sdiffsym, stereotype)
                other_qns = self._merge_in_order(
                    list(scope_a.get_rel_other_qns()),
                    list(scope_b.get_rel_other_qns()))
                for other_qn in other_qns:
                    rel_a = scope_a.get_rel(other_qn)
                    rel_b = scope_b.get_rel(other_qn)
                    rdiffsym = (" " if (rel_a and rel_b) else
                                "-" if rel_a else
                                "+")
                    reltype = rel_b and rel_b.type or rel_a.type
                    scope.add_rel(other_qn, reltype, rdiffsym)

                model[fname].add_scope(scope)
                for tname in tnames:
                    if (tname in scope_a.get_tag_keys()
                            and tname in scope_b.get_tag_keys()
                            and (scope_a.get_tag(tname) ==
                                 scope_b.get_tag(tname))):
                        scope.add_tag(copy.copy(scope_b.get_tag(tname)), " ")
                    else:
                        if tname in scope_a.get_tag_keys():
                            scope.add_tag(copy.copy(scope_a.get_tag(tname)),
                                          "-")
                        if tname in scope_b.get_tag_keys():
                            scope.add_tag(copy.copy(scope_b.get_tag(tname)),
                                          "+")
        return model

    def _merge_in_order(self, a, b):
        a2 = list(a)
        b2 = list(b)
        result = list()
        while len(a2) > 0:
            v1 = a2[0]
            if v1 in b2:
                while b2[0] != v1:
                    v2 = b2[0]
                    if v2 in a2:
                        a2.remove(v2)
                    b2.remove(v2)
                    result.append(v2)
            a2.remove(v1)
            if v1 in b2:
                b2.remove(v1)
            result.append(v1)
        return result + b2


class LineRange:
    def __init__(self, start, end):
        if start and not end:
            end = start
        self.start = start
        self.end = end
        self.valid = start and end

    def touching(a, b):
        return a and b and \
            a.valid and b.valid and \
            a.end >= b.start and b.end >= a.start
