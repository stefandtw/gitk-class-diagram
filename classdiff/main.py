#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
from classdiff.graphviz import GvGraph, GvFile, GvClass, GvRel
from classdiff.tag_model import ModelFactory
from classdiff.diff_range import DiffRangeFactory
from classdiff.config import Config


def main():
    Config.load_defaults()
    argparser = ArgumentParser(description="Create a class diagram as"
                               " Graphviz output based on ctags files and diff"
                               " line ranges")
    argparser.add_argument(dest="tagfile_a", help="first tags file or"
                           " directory", metavar="TAGS1")
    argparser.add_argument(dest="tagfile_b", help="second tags file or"
                           " directory", metavar="TAGS2")
    argparser.add_argument("-r", "--ranges", dest="rangesfile",
                           help="ranges file", metavar="RANGES")
    argparser.add_argument("-o", "--output", dest="outfile", help="write"
                           " output to file OUTPUT", metavar="OUTPUT")
    argparser.add_argument("-W", "--width", dest="width", type=int,
                           help="maximum pixel width of the generated diagram",
                           metavar="PX", default=10000)
    argparser.add_argument("-H", "--height", dest="height", type=int,
                           help="maximum pixel height of the generated"
                           " diagram", metavar="PX", default=10000)
    argparser.add_argument("-e", "--execute", dest="statements", type=str,
                           default=[], action="append", metavar="STATEMENT",
                           help="execute python statement to set config"
                           " variables")
    args = argparser.parse_args()

    if args.statements:
        for e in args.statements:
            exec(e)

    if args.outfile:
        sys.stdout = open(args.outfile, 'w')

    modelfactory = ModelFactory()
    model_a = modelfactory.fromfile(args.tagfile_a)
    model_b = modelfactory.fromfile(args.tagfile_b)
    model = modelfactory.diff(model_a, model_b)

    rangefactory = DiffRangeFactory()
    rangefactory.fromfile(args.rangesfile, model)
    model.mark_changed_members()

    gr = GvGraph(args.width, args.height)
    for fname in model:
        file = model[fname]
        f = GvFile(file)
        gr.add_file(f)
        scopes = file.get_scopes()
        for scope in scopes:
            if (scope.is_global_scope() and scope.is_empty()
                    and len(scopes) > 1):
                continue
            cl = GvClass(scope)
            f.add_class(cl)
    for fname in model:
        file = model[fname]
        for scope in file.get_scopes():
            for rel in scope.rels:
                other = model.get_scope(rel.other_qn)
                other_file = model.get_file_by_scope(rel.other_qn)

                def should_rel_use_file(file, scope):
                    if scope.is_global_scope():
                        visible = file.get_scope_count()
                        if scope.is_empty() and file.get_scope_count() > 1:
                            visible -= 1
                        return (visible > 1)
                a_use_file = should_rel_use_file(file, scope)
                b_use_file = should_rel_use_file(other_file, other)
                gvrel = GvRel(scope.qualified_name, a_use_file,
                              other.qualified_name, b_use_file,
                              rel.diffsym, rel.type)
                gr.add_rel(gvrel)

    gr.print()
    if args.outfile:
        sys.stdout.close()


if __name__ == "__main__":
    main()
