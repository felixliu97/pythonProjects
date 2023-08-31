import xmlschema

xsd_file = 'example.xsd'
xml_file = 'example.xml'

validator = xmlschema.XMLSchema(xsd_file)

if validator.is_valid(xml_file):
    print("XML is valid against the XSD.")
else:
    print("XML is not valid against the XSD.")
    print("Validation errors:")
    for error in validator.validate(xml_file):
        print(error)
