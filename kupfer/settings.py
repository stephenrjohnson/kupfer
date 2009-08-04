import os, sys
import ConfigParser

from kupfer import config, pretty

class SettingsController (pretty.OutputMixin):
	config_filename = "kupfer.cfg"
	defaults_filename = "defaults.cfg"
	sep = ";"
	default_directories = ("~/", "~/Desktop", )
	# Minimal "defaults" to define all fields
	# Read defaults defined in a defaults.cfg file
	defaults = {
		"Kupfer": { "keybinding" : "" , "showstatusicon" : "true" },
		"Plugins": { "direct" : (), "catalog" : (), },
		"Directories" : { "direct" : default_directories, "catalog" : (), },
		"DeepDirectories" : { "direct" : (), "catalog" : (), "depth" : 1, },
	}
	def __init__(self):
		self._config = self._read_config()
	def _read_config(self):
		"""
		Read cascading config files
		default -> then config
		(in all XDG_CONFIG_DIRS)
		"""
		parser = ConfigParser.SafeConfigParser()

		def fill_parser(parser, defaults):
			for secname, section in defaults.iteritems():
				if not parser.has_section(secname):
					parser.add_section(secname)
				for key, default in section.iteritems():
					if isinstance(default, (tuple, list)):
						default = self.sep.join(default)
					elif isinstance(default, int):
						default = str(default)
					parser.set(secname, key, default)

		# Set up defaults
		confmap = dict(self.defaults)
		fill_parser(parser, confmap)

		# Read all config files
		config_files = []
		defaults_path = config.get_data_file(self.defaults_filename)
		if not defaults_path:
			# try local file
			defaults_path = os.path.join("data", self.defaults_filename)
		if not os.path.exists(defaults_path):
			print "Error: no default config file %s found!" % self.defaults_filename
		else:
			config_files += (defaults_path, )

		config_path = config.get_config_file(self.config_filename)
		if config_path:
			config_files += (config_path, )

		for config_file in config_files:
			try:
				fil = open(config_file, "r")
				parser.readfp(fil)
				fil.close()
			except IOError, e:
				print "Error reading configuration file %s: %s", (config_file, e)

		# Read parsed file into the dictionary again
		for secname in parser.sections():
			if secname not in confmap: confmap[secname] = {}
			for key in parser.options(secname):
				value = parser.get(secname, key)
				retval = value
				if secname in self.defaults and key in self.defaults[secname]:
					defval = self.defaults[secname][key]
					if isinstance(defval, (tuple, list)):
						if not value:
							retval = ()
						else:
							retval = [p.strip() for p in value.split(self.sep) if p]
					elif isinstance(defval, int):
						retval = type(defval)(value)
					else:
						retval = str(value)
				confmap[secname][key] = retval

		return confmap
	def get_config(self, section, key):
		"""General interface, but section must exist"""
		key = key.lower()
		value = self._config[section].get(key)
		if section in self.defaults and key in self.defaults[section]:
			return value
		else:
			self.output_info("Settings key", section, key, "is invalid")

	def _get_raw_config(self, section, key):
		"""General interface, but section must exist"""
		key = key.lower()
		value = self._config[section].get(key)
		return value

	def get_plugin_enabled(self, plugin_id):
		return (plugin_id in self.get_config("Plugins", "Direct") or
			plugin_id in self.get_config("Plugins", "Catalog"))

	def get_plugin_config(self, plugin, key, value_type=str):
		"""Return setting @key for plugin names @plugin, try
		to coerce to type @value_type.
		Else return None if does not exist, or can't be coerced
		"""
		plug_section = "plugin_%s" % plugin
		if not plug_section in self._config:
			return None
		val = self._get_raw_config(plug_section, key)

		try:
			val = value_type(val)
		except ValueError, err:
			self.output_info("Error for stored value %s.%s" %
					(plug_section, key), err)
			return None
		self.output_debug("%s.%s = %s" % (plug_section, key, val))
		return val

_settings_controller = None
def GetSettingsController():
	global _settings_controller
	if _settings_controller is None:
		_settings_controller = SettingsController()
	return _settings_controller
