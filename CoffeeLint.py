import os
import sublime
import sublime_plugin
import subprocess
import tempfile

TYPE_PANEL_NAME = 'CoffeeLintPanel'

def call_exe(command):
    try:
        extended_env = dict(os.environ)
        extended_env['PATH'] = os.getenv('PATH').encode('utf-8', 'ignore')
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=extended_env,
            shell=True,
            universal_newlines=True)
        stdout, stderr = process.communicate()
        exit_code = process.wait()
        return stdout.decode('utf8')
    except OSError, e:
        if e.errno == errno.ENOENT:
            sublime.error_message("CoffeeLint: coffeelint not found. Please install 'coffeelint' npm package")

def call_exe_with_temp_file(command, content):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(content.encode('utf8'))
    temp_file.close()
    command.append(temp_file.name)
    result = call_exe(command)
    os.unlink(temp_file.name)
    return result

def show_output_panel(self, view, text):
    output_view = view.window().get_output_panel(TYPE_PANEL_NAME)
    output_view.set_read_only(False)
    output_view.sel().clear()
    edit = output_view.begin_edit()
    output_view.insert(edit, 0, text)
    output_view.end_edit(edit)
    output_view.set_read_only(True)
    view.window().run_command('show_panel', {'panel': 'output.' + TYPE_PANEL_NAME})

class CoffeeLintCodeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selection = sublime.Region(0, self.view.size())
        dirname, _ = os.path.split(os.path.abspath(__file__))
        config = os.path.join(dirname, 'config.json')
        result = call_exe_with_temp_file(['coffeelint', '--nocolor', '-f', config], self.view.substr(selection))
        data="\n".join(result.split('\n')[2:-1])
        show_output_panel(self, self.view, data)