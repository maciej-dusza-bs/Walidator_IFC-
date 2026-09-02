INVALID_HEADER_IFC = b"NOT-ISO-FILE;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-NOT-ISO;\n"

NO_FILE_SCHEMA_IFC = (
  b"ISO-10303-21;\n"
  b"HEADER;\n"
  b"FILE_DESCRIPTION((''),'2;1');\n"
  b"FILE_NAME('test','2024-01-01',(''),(''),'','','');\n"
  b"ENDSEC;\n"
  b"DATA;\n"
  b"ENDSEC;\n"
  b"END-ISO-10303-21;\n"
)

CORRUPT_IFC = (
  b"ISO-10303-21;\n"
  b"HEADER;\n"
  b"FILE_SCHEMA(('IFC2X3'));\n"
  b"ENDSEC;\n"
  b"DATA;\n"
  b"#1=THIS_IS_NOT_VALID_IFC;\n"
  b"ENDSEC;\n"
  b"END-ISO-10303-21;\n"
)

TOO_SMALL_IFC = b"1234567"
