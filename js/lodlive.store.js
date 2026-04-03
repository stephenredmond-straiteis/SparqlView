/**
 * lodliveStore - thin wrapper around native localStorage
 * Replaces jquery.jStorage with the same API: get, set, deleteKey, index.
 * Values are JSON-serialized automatically.
 */
var lodliveStore = (function() {
	return {
		get: function(key, defaultValue) {
			var raw = localStorage.getItem(key);
			if (raw === null) {
				return defaultValue !== undefined ? defaultValue : null;
			}
			try {
				return JSON.parse(raw);
			} catch (e) {
				return raw;
			}
		},
		set: function(key, value) {
			localStorage.setItem(key, JSON.stringify(value));
		},
		deleteKey: function(key) {
			localStorage.removeItem(key);
		},
		index: function() {
			var keys = [];
			for (var i = 0; i < localStorage.length; i++) {
				keys.push(localStorage.key(i));
			}
			return keys;
		}
	};
})();
