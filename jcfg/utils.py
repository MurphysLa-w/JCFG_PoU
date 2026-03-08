# Util Functions

def to_float_safe(value):
	if value is None:
		return None
	
	if isinstance(value, float):
		return value
	
	if isinstance(value, int):
		return float(value)
	
	if isinstance(value, str):
		value = value.strip().replace(",", ".")
		try:
			return float(value)
		except ValueError:
			return None
	
	return None

def to_str_safe(value):
	if value is None:
		return "nan"
	
	elif isinstance(value, str):
		if value.lower() in ("nan", ""):
			return "nan"
		else:
			return str(value)
	
	else:
		try:
			spl = str(value).split("e")
			res = spl[0] + " \\cdot 10^{" + spl[1] + "}"
			return res
		except:
			return str(value)
