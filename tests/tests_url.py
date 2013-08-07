import unittest

from phpdev import parse_url

class TestParseURL(unittest.TestCase):
    def test_parse_url_simple(self):
        file_path, path_info, query_string = parse_url('/index.php')
        assert file_path == 'index.php', file_path
        assert path_info == '', path_info
        assert query_string == '', query_string

    def test_parse_url_path_info(self):
        file_path, path_info, query_string = parse_url('/index.php/hello')
        assert file_path == 'index.php', file_path
        assert path_info == 'hello', path_info
        assert query_string == '', query_string

    def test_parse_url_long_path_info(self):
        file_path, path_info, query_string = parse_url('/path/to/index.php/hello')
        assert file_path == 'path/to/index.php', file_path
        assert path_info == 'hello', path_info
        assert query_string == '', query_string

    def test_parse_url_long_path_info_long(self):
        file_path, path_info, query_string = parse_url('/path/to/index.php/hello/there')
        assert file_path == 'path/to/index.php', file_path
        assert path_info == 'hello/there', path_info
        assert query_string == '', query_string

    def test_parse_url_simple_query(self):
        file_path, path_info, query_string = parse_url('/index.php?name=ali')
        assert file_path == 'index.php', file_path
        assert path_info == '', path_info
        assert query_string == 'name=ali', query_string

    def test_parse_url_path_info_query(self):
        file_path, path_info, query_string = parse_url('/index.php/hello?name=ali')
        assert file_path == 'index.php', file_path
        assert path_info == 'hello', path_info
        assert query_string == 'name=ali', query_string

if __name__ == '__main__':
    unittest.main()
