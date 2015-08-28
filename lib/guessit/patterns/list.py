import re
from guessit.patterns import sep, build_or_pattern
from guessit.patterns.numeral import parse_numeral

range_separators = ['-', 'to', 'a']
discrete_separators = ['&', 'and', 'et']
excluded_separators = ['.']  # Dot cannot serve as a discrete_separator

discrete_sep = sep
for range_separator in range_separators:
    discrete_sep = discrete_sep.replace(range_separator, '')
for excluded_separator in excluded_separators:
    discrete_sep = discrete_sep.replace(excluded_separator, '')
discrete_separators.append(discrete_sep)
all_separators = list(range_separators)
all_separators.extend(discrete_separators)

range_separators_re = re.compile(build_or_pattern(range_separators), re.IGNORECASE)
discrete_separators_re = re.compile(build_or_pattern(discrete_separators), re.IGNORECASE)
all_separators_re = re.compile(build_or_pattern(all_separators), re.IGNORECASE)


def list_parser(value, property_list_name, discrete_separators_re=discrete_separators_re, range_separators_re=range_separators_re, allow_discrete=False, fill_gaps=False):
    discrete_elements = filter(lambda x: x != '', discrete_separators_re.split(value))
    discrete_elements = [x.strip() for x in discrete_elements]

    proper_discrete_elements = []
    i = 0
    while i < len(discrete_elements):
        if i < len(discrete_elements) - 2 and range_separators_re.match(discrete_elements[i+1]):
            proper_discrete_elements.append(discrete_elements[i] + discrete_elements[i+1] + discrete_elements[i+2])
            i += 3
        else:
            match = range_separators_re.search(discrete_elements[i])
            if match and match.start() == 0:
                proper_discrete_elements[i - 1] += discrete_elements[i]
            elif match and match.end() == len(discrete_elements[i]):
                proper_discrete_elements.append(discrete_elements[i] + discrete_elements[i + 1])
            else:
                proper_discrete_elements.append(discrete_elements[i])
            i += 1

    discrete_elements = proper_discrete_elements

    ret = []

    for discrete_element in discrete_elements:
        range_values = filter(lambda x: x != '', range_separators_re.split(discrete_element))
        range_values = [x.strip() for x in range_values]
        if len(range_values) > 1:
            for x in range(0, len(range_values) - 1):
                start_range_ep = parse_numeral(range_values[x])
                end_range_ep = parse_numeral(range_values[x+1])
                for range_ep in range(start_range_ep, end_range_ep + 1):
                    if range_ep not in ret:
                        ret.append(range_ep)
        else:
            discrete_value = parse_numeral(discrete_element)
            if discrete_value not in ret:
                ret.append(discrete_value)

    if len(ret) > 1:
        if not allow_discrete:
            valid_ret = list()
            # replace discrete elements by ranges
            valid_ret.append(ret[0])
            for i in range(0, len(ret) - 1):
                previous = valid_ret[len(valid_ret) - 1]
                if ret[i+1] < previous:
                    pass
                else:
                    valid_ret.append(ret[i+1])
            ret = valid_ret
        if fill_gaps:
            ret = list(range(min(ret), max(ret) + 1))
        if len(ret) > 1:
            return {None: ret[0], property_list_name: ret}
    if len(ret) > 0:
        return ret[0]
    return None