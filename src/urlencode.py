def patchup(str):
	if "%" in str:
		str = str.replace("%","%25")
	if "=" in str:
		str = str.replace("=","%3D")
	if "&" in str:
		str = str.replace("&","%26")
	return str
def urlencode(dictIn):
	outstr = ""
	for key in dictIn:
		val = dictIn[key]

		key = patchup(key)
		outstr += key
		outstr += "="
		val = patchup(str(val))
		outstr += val
		outstr += "&"

	outstr = outstr [:-1]
	return outstr
