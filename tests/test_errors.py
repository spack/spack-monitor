"""
test spackmon errors upload
"""

import os
import sys

# Add spackmoncli to the path
test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, test_dir)
base = os.path.dirname(test_dir)
specs_dir = os.path.join(base, "specs")

from base import SpackMonitorTest

# Examples of errors to learn from
# this means we are adding to the database with metadata

learn_errors = [
    # This is the simplest example of an error we can add - we require a text field
    {"text": "error: Vanessasaur is a dinosaur, found 'turtle'"},
    # This is an extended version of that, add some custom metadata
    {
        "text": "error: Gil is a fish, found 'human'",
        "meta": {"library": "humans", "version": 1.2},
    },
    # This is a "traditional" set of error fields by the ctest parser
    # You can choose to add meta to this (or not)
    {
        "id": 3246,
        "phase": 1601,
        "source_file": "./boost/log/detail/light_function.hpp",
        "source_line_no": 442,
        "line_no": 28199,
        "repeat_count": 0,
        "start": 28193,
        "end": 28206,
        "text": "./boost/log/detail/light_function.hpp:442:38: warning: variadic templates only available with '-std=c++11' or '-std=gnu++11'",
        "pre_context": "./boost/log/detail/light_function.hpp:279:54: warning: variadic templates only available with '-std=c++11' or '-std=gnu++11'\n  279 |         typedef void (*invoke_type)(impl_base*, ArgsT...);\n      |                                                      ^~~\n./boost/log/detail/light_function.hpp:331:66: warning: variadic templates only available with '-std=c++11' or '-std=gnu++11'\n  331 |         static result_type invoke_impl(impl_base* self, ArgsT... args)\n      |                                                                  ^~~~",
        "post_context": "  442 |     result_type operator() (ArgsT... args) const\n      |                                      ^~~~\nIn file included from ./boost/log/sinks/unlocked_frontend.hpp:22,\n                 from ./boost/log/sinks.hpp:22,\n                 from libs/log/src/init_from_settings.cpp:47:\n./boost/log/detail/parameter_tools.hpp:77:35: warning: variadic templates only available with '-std=c++11' or '-std=gnu++11'",
        "add_date": "2021-08-09T21:36:21.333961Z",
        "modify_date": "2021-08-09T21:36:21.333984Z",
        "label": "build-error",
        "spack-monitor-label": "warning",
    },
]


class ErrorsTest(SpackMonitorTest):

    def test_errors(self):
        """Test uploading errors.
        """
        response = self.client.post("/ms1/errors/new/", data=learn_errors)
        assert response.status_code == 200

        res = response.json()
        assert "Successful" in res['message']
        assert "error_ids" in res
        print(res)
