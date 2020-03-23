import sys

from prov import dot as provo_dot

from noworkflow.now.utils.io import print_msg


def persist_document(document, name, format, extension, hide_elem_attr, hide_rel_attr, dir):
    print_msg("  Persisting collected provenance to local storage")

    filename = "{}{}".format(name, extension)
    serializers = ["json", "rdf", "provn", "turtle", "rdfxml", "trig", "xml"]
    rdf_serializers = {"turtle": "turtle", "rdfxml": "xml", "trig": "trig"}
    writers = ["dot", "jpeg", "png", "svg", "pdf"]

    if format in serializers:
        print_msg("    Employing serializer to export to {}".format(format))
        with open(filename, 'w') as file:
            if format in rdf_serializers:
                document.serialize(destination=file, format="rdf", rdf_format=rdf_serializers[format])
            else:
                document.serialize(destination=file, format=format)

    elif format in writers:
        print_msg("    Employing dot writer to export to {}".format(format))
        provo_dot.prov_to_dot(document, show_element_attributes=not hide_elem_attr, direction=dir,
                              show_relation_attributes=not hide_rel_attr).write(filename, format=format)

    else:
        print_msg("  Could not find suitable exporting module for {{name=\"{}\", format=\"{}\", extension=\"{}\"}}. "
                  "Try different input parameters.".format(name, format, extension))
        sys.exit(1)

    print_msg("Export to file \"{}\" done.".format(filename), force=True)
