import sublime

def get_setting(view, key, default=None):
    if view:
        settings = view.settings()
        if settings.has(key):
            return settings.get(key)
    settings = sublime.load_settings('CMakeBuilder.sublime-settings')
    return settings.get(key, default)
