from jpylyzer.jpylyzer import checkOneFile

def verify_jp2(image_file):
    jp2_element = checkOneFile(image_file)
    success = jp2_element.findtext('isValidJP2') == 'True'
    if not success:
        print(image_file + 'failed jypylzer validation:')
        print jp2_element
    return success
