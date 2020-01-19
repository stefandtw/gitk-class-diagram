import html
import re
from classdiff.tag_model import RelType


show_attr_type = True
show_op_return_type = False
show_visibility = True
show_single_scope_file_border = False
font = "Roboto, Verdana, Arial"
font_size_classname = 18
font_size_other = 11
bg_removed = "#ffaaaa"
bg_added = "#aaffaa"
bg_changed = "#ddf3ff"
bg_neutral = "#fff3d0"
fg_removed = "#dd0000"
fg_added = "#00dd00"
# Higher maxiter produces better layouts, but also takes more time.
maxiter = 600
# Big graphs are slow because of splines=compound. Don't use it if graphs are
# bigger than X.
splines_threshold = 5000


class Gv:
    def nodename(original):
        return re.sub(r"[^a-zA-Z]", "_", original)

    def clustername(original):
        return "cluster_" + Gv.nodename(original)

    def htmlesc(s):
        return html.escape(s)

    def bgcolor(diffsym, attr_name="bgcolor"):
        if diffsym == "-":
            return f" {attr_name}=\"{bg_removed}\""
        elif diffsym == "+":
            return f" {attr_name}=\"{bg_added}\""
        elif diffsym == "~":
            return f" {attr_name}=\"{bg_changed}\""
        else:
            return ""

    def fgcolor(diffsym, attr_name="color"):
        if diffsym == "-":
            return f" {attr_name}=\"{fg_removed}\""
        elif diffsym == "+":
            return f" {attr_name}=\"{fg_added}\""
        else:
            return ""

    def search_href(s):
        return f"href=\"gitk:search_next {{{Gv.htmlesc(s)}}}\""

    def file_href(file):
        return ("href=\""
                f"filename:{Gv.htmlesc(file)}:"
                f"gitk:scroll_to_file {{{Gv.htmlesc(file)}}}\"")

    def px_to_inches(s):
        gv_default_dpi = 96.0
        return str(float(s) / gv_default_dpi)


class GvBuilder:
    def __init__(self):
        self.steps = []
        self.end_steps = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        end_step = self.end_steps.pop()
        self.steps.append(end_step)

    def build(self):
        return "".join(self.steps)

    def text(self, content, end=None):
        self.steps.append(content)
        if end:
            self.end_steps.append(end)
        return self

    def digraph(self, name):
        return self.text(f"digraph {name} {{", "}\n")

    def cluster(self, name, attr):
        return self.text(f"""subgraph {Gv.clustername(name)} {{
    style=dotted;
    {attr};
""", "}\n")

    def node(self, name, attr):
        return self.text(Gv.nodename(name) + " [label=<", f"> {attr}]\n")

    def edge(self, a, b, attr=""):
        return self.text(f"{a} -> {b} [{attr}]\n")

    def html(self, tag_name, attr="", line_break=False):
        if attr:
            attr = " " + attr
        prefix = "\n" if line_break else ""
        start = f"{prefix}<{tag_name}{attr}>"
        self.steps.append(start)
        self.end_steps.append(f"</{tag_name}>")
        return self

    def htmltext(self, content, end=None):
        return self.text(Gv.htmlesc(content), end)

    def table(self, attr=""):
        return self.html("table", attr)

    def tr(self):
        return self.html("tr", line_break=True)

    def td(self, attr=""):
        return self.html("td", attr)

    def font(self, attr=""):
        return self.html("font", attr)

    def b(self):
        return self.html("b")

    def i(self):
        return self.html("i")

    def u(self):
        return self.html("u")


class GvGraph:
    def __init__(self, width_inches, height_inches):
        self.width_inches = Gv.px_to_inches(width_inches)
        self.height_inches = Gv.px_to_inches(height_inches)
        self.files = []
        self.rels = []

    def add_file(self, f):
        self.files.append(f)

    def add_rel(self, rel):
        self.rels.append(rel)

    def get_rels(self, type):
        return [rel for rel in self.rels if rel.type == type]

    def _splines(self):
        if len(self.rels)**2 * len(self.files) \
                > splines_threshold:
            return "curved"
        return "compound"

    def print(self):
        with GvBuilder().digraph("cl") as b:
            b.text(f"""
    size=\"{self.width_inches},{self.height_inches}\";
    ratio=collapse;
    outputorder=edgesfirst;
    maxiter={maxiter};
    splines={self._splines()};
    node [shape=none margin=0 style=filled fillcolor="{bg_neutral}"
        fontname="{font}" fontsize={font_size_other}];
    edge [arrowhead=open]""")
            b.text("\n")
            self._print_files(b)
            self._print_rels(b)
        print(b.build())

    def _print_files(self, b):
        for f in self.files:
            f.print(b)

    def _print_rels(self, b):
        assocs = self.get_rels(RelType.ASSOC)
        derivs = self.get_rels(RelType.DERIV)
        reals = self.get_rels(RelType.REAL)
        for rel in assocs:
            rel.print(b)
        if derivs or reals:
            b.text("    edge [arrowhead=empty];\n")
        for rel in derivs:
            rel.print(b)
        if reals:
            b.text("    edge [style=dashed];\n")
        for rel in reals:
            rel.print(b)


class GvFile:
    def __init__(self, file):
        self.classes = []
        self.name = file.name

    def add_class(self, cl):
        self.classes.append(cl)

    def print(self, b):
        with b.cluster(self.name,  Gv.file_href(self.name)):
            with b.text("    label=<", ">;\n"):
                with b.table("cellspacing=\"0\" cellpadding=\"0\""
                             " border=\"0\""):
                    with b.tr():
                        with b.td(Gv.search_href(self.name)):
                            b.htmltext(self.name)
            if not show_single_scope_file_border and len(self.classes) == 1:
                b.text("    style=invis;\n")
                b.text("    label=\"\";\n")
            for cl in self.classes:
                cl.print(b)


class GvClass:
    def __init__(self, scope):
        self.diffsym = scope.diffsym
        self.label = scope.name if scope.name != "" else scope.qualified_name
        self.qualified_name = scope.qualified_name
        self.attrs = scope.get_attrs()
        self.ops = scope.get_ops()
        self.stereotype = scope.stereotype
        self.fake = scope.is_global_scope()

    def print(self, b):
        fillcolor = Gv.bgcolor(self.diffsym, "fillcolor")
        style = " style=\"dashed\"" if self.fake else ""
        with b.node(self.qualified_name, fillcolor):
            with b.table("cellspacing=\"0\" cellpadding=\"1\"" + style):
                with b.tr():
                    with b.td(Gv.search_href(self.label) + " sides=\"b\""):
                        self._print_name(b)
                self._print_attrs(b)
                with b.tr():
                    with b.td("sides=\"b\""):
                        pass
                self._print_ops(b)

    def _print_name(self, b):
        if self.stereotype:
            with b.font(f"point-size=\"{font_size_other!s}\""):
                b.htmltext(f"<<{self.stereotype}>>")
                b.text("<br/>")
        split = self.label.rsplit("/", 1)
        name = split[-1]
        dir = split[0] + "/" if len(split) == 2 else ""
        if dir:
            with b.font(f"point-size=\"{font_size_other!s}\""):
                with b.html("sup"):
                    b.htmltext(dir)
                b.text("<br/>")
        with b.font(f"point-size=\"{font_size_classname!s}\""):
            with b.b():
                b.htmltext(name)

    def _print_attrs(self, b):
        tags = self._limit(self.attrs)
        self._print_tags(tags, show_attr_type, b)

    def _print_ops(self, b):
        tags = self._limit(self.ops)
        self._print_tags(tags, show_op_return_type, b, "()")

    def _limit(self, tags, limit=10):
        if len(tags) > limit:
            tags = tags.copy()
            # Cut off unchanged tags, starting from the end
            for i in reversed(range(len(tags))):
                if tags[i].diffsym == " ":
                    tags.pop(i)
                    if len(tags) == limit:
                        break
            # Cut off remaining changed tags
            tags = tags[:limit]
            tags.append("...")
        return tags

    def _print_tags(self, tags, show_type_ref, b, suffix=""):
        num = 0
        for tag in tags:
            if tag == "...":
                with b.tr():
                    with b.td("border=\"0\" align=\"left\""):
                        b.text("...")
                break
            text = tag.visibility if show_visibility else ""
            text += tag.name
            text += suffix
            bgcolor = Gv.bgcolor(tag.diffsym)
            with b.tr():
                with b.td(f"border=\"0\" align=\"left\"{bgcolor} "
                          + Gv.search_href(tag.name)):
                    if tag.is_static:
                        with b.u():
                            b.htmltext(text)
                    else:
                        b.htmltext(text)
                    if show_type_ref and tag.typeref != "-":
                        with b.i():
                            b.htmltext(" : " + tag.typeref)
            num += 1


class GvRel:
    def __init__(self, a_qn, a_use_file, b_qn, b_use_file, diffsym, type):
        if a_use_file:
            self._a_name = Gv.clustername(a_qn)
        else:
            self._a_name = Gv.nodename(a_qn)
        if b_use_file:
            self._b_name = Gv.clustername(b_qn)
        else:
            self._b_name = Gv.nodename(b_qn)
        self.diffsym = diffsym
        self.type = type

    def print(self, b):
        attr = Gv.fgcolor(self.diffsym)
        b.edge(self._a_name, self._b_name, attr)
