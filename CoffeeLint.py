import os
import sublime
import sublime_plugin
import subprocess
import errno
import tempfile
import json

TYPE_PANEL_NAME = 'CoffeeLintPanel'

class CoffeeLintCodeCommand(sublime_plugin.TextCommand):
    def call_exe(self, command):
        try:
            extended_env = dict(os.environ)
            extended_env['PATH'] = os.getenv('PATH').encode('utf8', 'ignore')
            if self.settings.get('node_path') :
                extended_env['PATH'] += ':' + self.settings.get('node_path')
            if self.settings.get('coffeelint_path'):
                extended_env['PATH'] += ':' + self.settings.get('coffeelint_path')

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                env=extended_env,
                universal_newlines=True)

            stdout, stderr = process.communicate()
            exit_code = process.wait()
            return stdout.decode('utf8')
        except OSError, e:
            if e.errno == errno.ENOENT:
                sublime.error_message("CoffeeLint: coffeelint not found. Please install 'coffeelint' npm package")

    def call_exe_with_temp_file(self, command, content):
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(content.encode('utf8'))
        temp_file.close()
        config = self.create_create_config_file()
        command.append('-f')
        command.append(config.name)
        command.append(temp_file.name)
        result = self.call_exe(command)
        os.unlink(temp_file.name)
        os.unlink(config.name)
        return result

    def create_create_config_file(self):
        config = tempfile.NamedTemporaryFile(delete=False)
        lint_config = self.settings.get('lint_config')
        content = json.dumps(lint_config, sort_keys=True, indent=4, separators=(',', ':'))
        config.write(content)
        config.close()
        return config

    def show_output_panel(self, text):
        output_view = self.view.window().get_output_panel(TYPE_PANEL_NAME)
        output_view.set_read_only(False)
        output_view.sel().clear()
        edit = output_view.begin_edit()
        output_view.insert(edit, 0, text)
        output_view.end_edit(edit)
        output_view.set_read_only(True)
        self.view.window().run_command('show_panel', {'panel': 'output.' + TYPE_PANEL_NAME})


    def run(self, edit):
        self.settings = sublime.load_settings('CoffeeLint.sublime-settings')
        selection = sublime.Region(0, self.view.size())
        dirname, _ = os.path.split(os.path.abspath(__file__))
        config = os.path.join(dirname, 'config.json')
        result = self.call_exe_with_temp_file(['coffeelint', '--nocolor'], self.view.substr(selection))
        data="\n".join(result.split('\n')[1:-1])
        if data:
            self.show_output_panel(data)

