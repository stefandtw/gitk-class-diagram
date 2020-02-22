import re


class TagLanguage:
    def __init__(self, lang):
        self.lang = lang

    def is_blacklisted(self):
        return self.lang in ("XML", "Maven2", "Iniconf")

    def is_scope(self, kind, roles, access, name):
        if roles != "def":
            return False
        if self.lang in ("CSS", "SCSS"):
            return False
        return kind in ("class", "interface", "struct", "enum")

    def is_attr(self, kind, roles, access, name):
        if roles != "def":
            return False
        if self.lang in ("Asciidoc", "Markdown", "ReStructuredText"):
            return kind in ("chapter", "section")
        if self.lang in ("CSS", "SCSS"):
            return kind in ("class", "selector", "id")
        if self.lang in ("HTML", "XML"):
            return kind == "id"
        if self.lang == "Java":
            return kind in ("field", "enumConstant")
        if self.lang == "JavaProperties":
            return kind == "key"
        if self.lang == "Make":
            return kind == "target"
        if self.lang == "Python":
            return kind == "variable"
        if self.lang == "YACC":
            return kind == "label"
        return kind in ("field", "member", "enumerator")

    def is_op(self, kind, roles, access, name):
        if roles != "def":
            return False
        if self.lang == "Python":
            return kind == "member" or (kind == "function" and access ==
                                        "public")
        if self.lang == "JavaScript":
            return kind in ("function", "method") \
                and not name.startswith("AnonymousFunction")
        if self.lang == "XSLT":
            return kind in ("namedTemplate", "matchedTemplate")
        return kind in ("function", "func", "method", "procedure",
                        "subroutine")

    def is_inv_tag(self, kind, roles, access, name):
        # Expecting this not to be called for attrs and ops
        if self.lang == "Python" and roles == "def" and kind != "class":
            return False
        return True

    def get_scope_stereotype(self, kind, implementation):
        if implementation in ("abstract"):
            return implementation
        if kind in ("enum", "interface"):
            return kind
        return ""

    def is_static_member(self, kind, implementation):
        if self.lang == "JavaScript":
            return kind == "function"
        return False

    def name(self, original):
        if self.lang in ("C", "C++") and original.startswith("__anon"):
            return "<anonymous>"
        return original

    def typeref(self, original):
        if self.lang in ("C", "C++") and "__anon" in original:
            return re.sub(r"__anon\w*", "<anonymous>", original)
        return original.replace("typename:", "")

    def visibility(self, access):
        map = {"public": "+",
               "private": "-",
               "protected": "#",
               "package": "~"
               }
        if self.lang == "Java" and access == "default":
            return "~"
        return map[access] if access in map else ""

    def scope(self, original):
        if self.lang in ("C", "C++") and original.startswith("__anon"):
            return "<anonymous>"
        if self.lang in ("Go", "C#"):
            return re.sub(r"[^.]+\.?", "", original, count=1)
        if self.lang == "ReStructuredText":
            return ""
        return original

    def split_inherits(self, inherits):
        return inherits.split(", ")

    def is_nested(self, scope):
        return scope != "-" and scope != ""

    def only_works_with_nesting(self):
        if self.lang in ("Ruby"):
            return True
        return False

    def local_name(self, scope):
        return scope.split(".")[-1]
