from PyInstaller.utils.hooks import collect_data_files

datas = list()
datas += collect_data_files("itaxotools.abcd_validator")
datas += collect_data_files("abcd_converter_gfbio_org")
datas += collect_data_files("xmlschema")
