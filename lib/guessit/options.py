from argparse import ArgumentParser


def build_opts(transformers=None):
    opts = ArgumentParser()
    opts.add_argument(dest='filename', help='Filename or release name to guess', nargs='*')

    naming_opts = opts.add_argument_group("Naming")
    naming_opts.add_argument('-t', '--type', dest='type', default=None,
                             help='The suggested file type: movie, episode. If undefined, type will be guessed.')
    naming_opts.add_argument('-n', '--name-only', dest='name_only', action='store_true', default=False,
                             help='Parse files as name only. Disable folder parsing, extension parsing, and file content analysis.')
    naming_opts.add_argument('-c', '--split-camel', dest='split_camel', action='store_true', default=False,
                             help='Split camel case part of filename.')

    naming_opts.add_argument('-X', '--disabled-transformer', action='append', dest='disabled_transformers',
                             help='Transformer to disable (can be used multiple time)')

    output_opts = opts.add_argument_group("Output")
    output_opts.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                             help='Display debug output')
    output_opts.add_argument('-P', '--show-property', dest='show_property', default=None,
                             help='Display the value of a single property (title, series, videoCodec, year, type ...)'),
    output_opts.add_argument('-u', '--unidentified', dest='unidentified', action='store_true', default=False,
                             help='Display the unidentified parts.'),
    output_opts.add_argument('-a', '--advanced', dest='advanced', action='store_true', default=False,
                             help='Display advanced information for filename guesses, as json output')
    output_opts.add_argument('-y', '--yaml', dest='yaml', action='store_true', default=False,
                             help='Display information for filename guesses as yaml output (like unit-test)')
    output_opts.add_argument('-f', '--input-file', dest='input_file', default=False,
                             help='Read filenames from an input file.')
    output_opts.add_argument('-d', '--demo', action='store_true', dest='demo', default=False,
                             help='Run a few builtin tests instead of analyzing a file')

    information_opts = opts.add_argument_group("Information")
    information_opts.add_argument('-p', '--properties', dest='properties', action='store_true', default=False,
                                  help='Display properties that can be guessed.')
    information_opts.add_argument('-V', '--values', dest='values', action='store_true', default=False,
                                  help='Display property values that can be guessed.')
    information_opts.add_argument('-s', '--transformers', dest='transformers', action='store_true', default=False,
                                  help='Display transformers that can be used.')
    information_opts.add_argument('--version', dest='version', action='store_true', default=False,
                                  help='Display the guessit version.')

    webservice_opts = opts.add_argument_group("guessit.io")
    webservice_opts.add_argument('-b', '--bug', action='store_true', dest='submit_bug', default=False,
                                 help='Submit a wrong detection to the guessit.io service')

    other_opts = opts.add_argument_group("Other features")
    other_opts.add_argument('-i', '--info', dest='info', default='filename',
                            help='The desired information type: filename, video, hash_mpc or a hash from python\'s '
                            'hashlib module, such as hash_md5, hash_sha1, ...; or a list of any of '
                            'them, comma-separated')

    if transformers:
        for transformer in transformers:
            transformer.register_arguments(opts, naming_opts, output_opts, information_opts, webservice_opts, other_opts)

    return opts, naming_opts, output_opts, information_opts, webservice_opts, other_opts
_opts, _naming_opts, _output_opts, _information_opts, _webservice_opts, _other_opts = None, None, None, None, None, None


def reload(transformers=None):
    global _opts, _naming_opts, _output_opts, _information_opts, _webservice_opts, _other_opts
    _opts, _naming_opts, _output_opts, _information_opts, _webservice_opts, _other_opts = build_opts(transformers)


def get_opts():
    return _opts
