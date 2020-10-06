#!/usr/bin/env python
from dataclasses import dataclass
import pygments
import pygments.lexers as lexers
import pygments.formatters.html as formatters
import re
import html
pygment_lexer = lexers.get_lexer_for_filename("what.py")
pygment_format = formatters.HtmlFormatter()

def highlight(code):
    return pygments.highlight(code, pygment_lexer, pygment_format)


def gen_id(string):
    return string.split("(")[0].replace(".", "_")


def pretty_function_name(name):
    outer_match = re.search(r"(\w+)\((.*)\)", name)
    # If this is not a function, just return the raw name
    if outer_match is not None:
        fn_name = outer_match.group(1)
        arg_string = outer_match.group(2)

        args = []
        if arg_string:
            # Try to build a list of arguments
            comma_separated = arg_string.split(',')
            # Spliting on , has side effects when the default value has , in
            # it. We'll try to rectify that by re-joining string which don't
            # look like identifiers
            for part in comma_separated:
                # If this is a new argument
                arg_regex = re.search(r"([A-z_][0-9A-z_]*)(=?)(.*)", part)
                if arg_regex is not None:
                    arg_name = arg_regex.group(1)
                    if arg_regex.group(2) == '':
                        # If this is not a keyword arg, add it to the list:
                        args.append((arg_name, None))
                    else:
                        # This is a keyword arg, add it, along with a list of
                        # arguments.
                        args.append((arg_name, [arg_regex.group(3)]))
                else:
                    args[-1][1].append(part)

        def format_arg(arg):
            (name, default) = arg
            result = f"<span class='arg'>{name}</span>"
            if default:
                result += "<span class='eq'>=</span>"
                result += "<span class='default_arg'>"
                result += ", ".join(default)
                result += "</span>"
            return result

        # Pretty print everything
        result  = f"<span class='fn_name'>{fn_name}</span>"
        result += f"<span class='paren'>( </span>"
        result += "<span class='comma'>, </span>".join([format_arg(x) for x in args])
        result += f"<span class='paren'> )</span>"
        return result
    return name


def gen_doc(name, id_name, docstrings):
    def format_doc(i, x):
        if i == 0:
            classname = "docstr explain"
            prefix = "Description"
        else:
            classname = "docstr example"
            prefix = "Example"

        while True:
            start_glyph = "!--"
            end_glyph = "--!"
            if not (start_glyph in x and end_glyph in x):
                break
            block_start = x.index(start_glyph)
            cmd = x[block_start+len(start_glyph):x.index("\n", block_start)]
            block_end = x.index(end_glyph)
            block = x[block_start+len(start_glyph)+len(cmd):block_end]
            if cmd == "code":
                formatted = highlight(block).strip()
                x = x[:block_start] + formatted + x[block_end+len(end_glyph):]
            elif cmd == "params":
                params = re.findall(r"\[(.*)\]\W*([^\[]*)", block)
                params_prefix = "<table  class=\"args\">"
                params = [f"<tr><td><code>{param.strip()}</code></td><td>{comment.strip()}</td></tr>" for param, comment in params]
                params_suffix = "</table>"
                x = x[:block_start] + params_prefix + "\n".join(params) + params_suffix + x[block_end+len(end_glyph):]

        return f"<div class='{classname}'><div class='header {prefix}'>{prefix}</div><div class='content'>" + x.replace('\n\n', '<br>') + "</div></div>"

    if docstrings:
        title = pretty_function_name(name)
        out = "".join([format_doc(i, x) for i, x in enumerate(docstrings)])
        return f"<div id='{id_name}' class='func'><h2 class='title'>{title}</h2>{out}</div>"
    else:
        return f"<h2 id='{id_name}' class='constant'>{name}</h2>"

@dataclass
class Docs:
    name: str = "NO NAME"
    id_name: str = ""
    docs = None


def parse_docs(filename):
    with open(filename, "r") as f:
        res = []
        doc = Docs()
        block = ""
        for line in f:
            line = re.sub(r"`([^`]*)`", "<code>\g<1></code>", line)
            if line == "\n":
                line = "</p><p>"
            if line.startswith("# "):
                if block:
                    doc.docs.append(block + "</p>")
                    block = "<p>"
                    res.append(doc)

                doc = Docs()
                doc.docs = []
                doc.name = line[2:].strip()
                doc.id_name = gen_id(doc.name)
            elif line.startswith("## ex"):
                if block:
                    doc.docs.append(block + "</p>")
                    block = "<p>"
            else:
                block += line
        if block:
            doc.docs.append(block + "</p>")
            block = "<p>"
            res.append(doc)
        return res

def table_of_content_link(thing):
    target_id = html.escape(thing.id_name)

    # The name contains a leading code tag and arguments. Get rid of those
    name = html.escape(thing.name.split('(')[0].replace('<code>', ''))
    return f"<a href='#{target_id}'>{name}</a>"

def gen_table_of_content(pg, sr):
    html = "<div class='toc'>"
    html += "<svg class='logo' viewBox='0 0 112 45'>" +\
            open("ribs-logo.svg").read() +\
            "</svg>"
    html += "<h2>Table of Contents</h2>"
    html += "<br>".join(f"{table_of_content_link(x)}" for x in sr)
    html += "</div>"

    # Clsoe toc div
    html += "</div>"
    return html

style = open("style.css", "r").read()
style += pygment_format.get_style_defs()
sr_docs = parse_docs("ribs.docs")

toc = gen_table_of_content([], sr_docs)
with open("index.html", "w+") as f:
    intro = "<h1>Snake Ribs</h1><p>A small and simple PyGame wrapper, for getting started quick and easy.</p>"
    f.write("<!--- This file is auto generated, please do not edit -->")
    f.write(f"<html><head><title>Documentation</title><style>{style}</style></head><body>")
    f.write(toc)
    f.write("<main>")
    f.write(intro)
    f.write("<div id='lithekod'>")
    f.write("".join([gen_doc(x.name, x.id_name, x.docs) for x in sr_docs]))
    f.write("</div>")
    f.write("<footer>Made with <span class='heart'>&lt;3</span> by LiTHe-kod</footer>")
    f.write("</main>")
    f.write("</body></html>")
