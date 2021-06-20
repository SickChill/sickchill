# all regexes are case insensitive


normal_regexes = [
    (
        "standard_repeat",
        # Show.Name.S01E02.S01E03.Source.Quality.Etc-Group
        # Show Name - S01E02 - S01E03 - S01E04 - Ep Name
        r"""
     ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
     s(?P<season_num>\d+)[. _-]*                 # S01 and optional separator
     e(?P<ep_num>\d+)                            # E02 and separator
     ([. _-]+s(?P=season_num)[. _-]*             # S01 and optional separator
     e(?P<extra_ep_num>\d+))+                    # E03/etc and separator
     [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "fov_repeat",
        # Show.Name.1x02.1x03.Source.Quality.Etc-Group
        # Show Name - 1x02 - 1x03 - 1x04 - Ep Name
        r"""
     ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
     (?P<season_num>\d+)x                        # 1x
     (?P<ep_num>\d+)                             # 02 and separator
     ([. _-]+(?P=season_num)x                    # 1x
     (?P<extra_ep_num>\d+))+                     # 03/etc and separator
     [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "standard",
        # Show.Name.S01E02.Source.Quality.Etc-Group
        # Show Name - S01E02 - My Ep Name
        # Show.Name.S01.E03.My.Ep.Name
        # Show.Name.S01E02E03.Source.Quality.Etc-Group
        # Show Name - S01E02-03 - My Ep Name
        # Show.Name.S01.E02.E03
        r"""
     ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
     \(?s(?P<season_num>\d+)[. _-]*              # S01 and optional separator
     e(?P<ep_num>\d+)\)?                         # E02 and separator
     (([. _-]*e|-)                               # linking e/- char
     (?P<extra_ep_num>(?!(1080|720|480)[pi])\d+)(\))?)*   # additional E03/etc
     ([. _,-]+((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?)?$              # Group
     """,
    ),
    (
        "newpct",
        # American Horror Story - Temporada 4 HDTV x264[Cap.408_409]SPANISH AUDIO -NEWPCT
        # American Horror Story - Temporada 4 [HDTV][Cap.408][Espanol Castellano]
        # American Horror Story - Temporada 4 HDTV x264[Cap.408]SPANISH AUDIO –NEWPCT)
        r"""
     (?P<series_name>.+?).-.+\d{1,2}[ ,.]       # Show name: American Horror Story
     (?P<extra_info>.+)\[Cap\.                   # Quality: HDTV x264, [HDTV], HDTV x264
     (?P<season_num>\d{1,2})                     # Season Number: 4
     (?P<ep_num>\d{2})                           # Episode Number: 08
     ((_\d{1,2}(?P<extra_ep_num>\d{2}))|.*\])     # Episode number2: 09
     """,
    ),
    (
        "fov",
        # Show_Name.1x02.Source_Quality_Etc-Group
        # Show Name - 1x02 - My Ep Name
        # Show_Name.1x02x03x04.Source_Quality_Etc-Group
        # Show Name - 1x02-03-04 - My Ep Name
        r"""
     ^((?!\[.+?\])(?P<series_name>.+?)[\[. _-]+)?  # Show_Name and separator if no brackets group
     (?P<season_num>\d+)x                          # 1x
     (?P<ep_num>\d+)                               # 02 and separator
     (([. _-]*x|-)                                 # linking x/- char
     (?P<extra_ep_num>
     (?!(1080|720|480)[pi])(?!(?<=x)26[45])           # ignore obviously wrong multi-eps
     \d+))*                                        # additional x03/etc
     [\]. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                          # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "verbose",
        # Show Name Season 1 Episode 2 Ep Name
        r"""
     ^(?P<series_name>.+?)[. _-]+                # Show Name and separator
     (season|series)[. _-]+                      # season and separator
     (?P<season_num>\d+)[. _-]+                  # 1
     episode[. _-]+                              # episode and separator
     (?P<ep_num>\d+)[. _-]+                      # 02 and separator
     (?P<extra_info>.+)$                         # Source_Quality_Etc-
     """,
    ),
    (
        "scene_date_format",
        # Show.Name.2010.11.23.Source.Quality.Etc-Group
        # Show Name - 2010-11-23 - Ep Name
        r"""
     ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
     (?P<air_date>(\d+[. _-]\d+[. _-]\d+)|(\d+\w+[. _-]\w+[. _-]\d+))
     [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "scene_sports_format",
        # Show.Name.100.Event.2010.11.23.Source.Quality.Etc-Group
        # Show.Name.2010.11.23.Source.Quality.Etc-Group
        # Show Name - 2010-11-23 - Ep Name
        r"""
     ^(?P<series_name>.*?(UEFA|MLB|ESPN|WWE|MMA|UFC|TNA|EPL|NASCAR|NBA|NFL|NHL|NRL|PGA|SUPER LEAGUE|FORMULA|FIFA|NETBALL|MOTOGP).*?)[. _-]+
     ((?P<series_num>\d{1,4})[. _-]+)?
     (?P<air_date>(\d+[. _-]\d+[. _-]\d+)|(\d+\w+[. _-]\w+[. _-]\d+))[. _-]+
     ((?P<extra_info>.+?)((?<![. _-])
     (?<!WEB)-(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$
     """,
    ),
    (
        "stupid_with_denotative",
        # aaf-sns03e09
        # flhd-supernaturals07e02-1080p
        r"""
     (?P<release_group>.+?)(?<!WEB)-(?P<series_name>\w*)(?<!\d)[\. ]?   # aaf-sn
     (?!26[45])                                                            # don't count x264, x265
     s(?P<season_num>\d{1,2})                                           # s03
     e(?P<ep_num>\d{2})(?:(rp|-(1080p|720p)))?$                             # e09
     """,
    ),
    (
        "stupid",
        # tpz-abc102
        r"""
     (?P<release_group>.+?)(?<!WEB)-(?P<series_name>\w*)(?<!\d)[\. ]?   # tpz-abc
     (?!26[45])                                                            # don't count x264
     (?P<season_num>\d{1,2})                                            # 1
     (?P<ep_num>\d{2})$                                                 # 02
     """,
    ),
    (
        "season_only",
        # Show.Name.S01.Source.Quality.Etc-Group
        r"""
     ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
     s(eason[. _-])?                             # S01/Season 01
     (?P<season_num>\d+)[. _-]*                  # S01 and optional separator
     [. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "no_season_multi_ep",
        # Show.Name.E02-03
        # Show.Name.E02.2010
        r"""
     ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
     (e(p(isode)?)?|part|pt)[. _-]?              # e, ep, episode, or part
     (?P<ep_num>(\d+|(?<!e)[ivx]+))                    # first ep num
     ((([. _-]+(and|&|to)[. _-]+)|-)             # and/&/to joiner
     (?P<extra_ep_num>(?!(1080|720|480)[pi])(\d+|(?<!e)[ivx]+))[. _-])            # second ep num
     ([. _-]*(?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "no_season_general",
        # Show.Name.E23.Test
        # Show.Name.Part.3.Source.Quality.Etc-Group
        # Show.Name.Part.1.and.Part.2.Blah-Group
        r"""
     ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
     (e(p(isode)?)?|part|pt)[. _-]?              # e, ep, episode, or part
     (?P<ep_num>(\d+|((?<!e)[ivx]+(?=[. _-]))))                    # first ep num
     ([. _-]+((and|&|to)[. _-]+)?                # and/&/to joiner
     ((e(p(isode)?)?|part|pt)[. _-]?)           # e, ep, episode, or part
     (?P<extra_ep_num>(?!(1080|720|480)[pi])
     (\d+|((?<!e)[ivx]+(?=[. _-]))))[. _-])*            # second ep num
     ([. _-]*(?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "bare",
        # Show.Name.102.Source.Quality.Etc-Group
        r"""
     ^(?P<series_name>.+?)[. _-]+                # Show_Name and separator
     (?P<season_num>\d{1,2})                     # 1
     (e?)                                        # Optional episode separator
     (?P<ep_num>\d{2})                           # 02 and separator
     ([. _-]+(?P<extra_info>(?!\d{3}[. _-]+)[^-]+) # Source_Quality_Etc-
     (-(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$                # Group
     """,
    ),
    (
        "no_season",
        # Show Name - 01 - Ep Name
        # 01 - Ep Name
        # 01 - Ep Name
        r"""
     ^((?P<series_name>.+?)(?:[. _-]{2,}|[. _]))?    # Show_Name and separator
     (?P<ep_num>\d{1,4})                             # 02
     (?:-(?P<extra_ep_num>\d{1,4}))*                 # -03-04-05 etc
     (\s*(?:of)?\s*\d{1,4})?                         # of joiner (with or without spaces) and series total ep
     [. _-]+((?P<extra_info>.+?)                     # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                            # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$  # Group
     """,
    ),
]

anime_regexes = [
    (
        "anime_horriblesubs",
        # [HorribleSubs] Maria the Virgin Witch - 01 [720p].mkv
        r"""
     ^(?:\[(?P<release_group>HorribleSubs)\][\s\.])
     (?:(?P<series_name>.+?)[\s\.]-[\s\.])
     (?P<ep_ab_num>((?!(1080|720|480)[pi]))\d{1,4})
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?
     (?:v(?P<version>[0-9]))?
     (?:[\w\.\s]*)
     (?:(?:(?:[\[\(])(?P<extra_info>\d{3,4}[xp]?\d{0,4}[\.\w\s-]*)(?:[\]\)]))|(?:\d{3,4}[xp]))
     .*?
     """,
    ),
    (
        "anime_ultimate",
        r"""
     ^(?:\[(?P<release_group>.+?)\][ ._-]*)
     (?P<series_name>.+?)[ ._-]+
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?[ ._-]+?
     (?:v(?P<version>[0-9]))?
     (?:[\w\.]*)
     (?:(?:(?:[\[\(])(?P<extra_info>\d{3,4}[xp]?\d{0,4}[\.\w\s-]*)(?:[\]\)]))|(?:\d{3,4}[xp]))
     (?:[ ._]?\[(?P<crc>\w+)\])?
     .*?
     """,
    ),
    (
        "anime_french_fansub",
        # [Kaerizaki-Fansub]_One_Piece_727_[VOSTFR][HD_1280x720].mp4
        # [Titania-Fansub]_Fairy_Tail_269_[VOSTFR]_[720p]_[1921E00C].mp4
        # [ISLAND]One_Piece_726_[VOSTFR]_[V1]_[8bit]_[720p]_[2F7B3FA2].mp4
        # Naruto Shippuden 445 VOSTFR par Fansub-Resistance (1280*720) - version MQ
        # Dragon Ball Super 015 VOSTFR par Fansub-Resistance (1280x720) - HQ version
        # [Mystic.Z-Team].Dragon.Ball.Super.-.épisode.36.VOSTFR.720p
        # [Z-Team][DBSuper.pw] Dragon Ball Super - 028 (VOSTFR)(720p AAC)(MP4)
        # [SnF] Shokugeki no Souma - 24 VOSTFR [720p][41761A60].mkv
        # [Y-F] Ao no Kanata no Four Rhythm - 03 Vostfr HD 8bits
        # Phantasy Star Online 2 - The Animation 04 vostfr FHD
        # Detective Conan 804 vostfr HD
        # Active Raid 04 vostfr [1080p]
        # Sekko Boys 04 vostfr [720p]
        r"""
     ^(\[(?P<release_group>.+?)\][ ._-]*)?                                                     # Release Group and separator (Optional)
     ((\[|\().+?(\]|\))[ ._-]*)?                                                               # Extra info (Optionnal)
     (?P<series_name>.+?)[ ._-]+                                                               # Show_Name and separator
     ((épisode|episode|Episode)[ ._-]+)?                                                       # Sentence for special fansub (Optionnal)
     (?P<ep_ab_num>\d{1,4})[ ._-]+                                                             # Episode number and separator
     (((\[|\())?(VOSTFR|vostfr|Vostfr|VostFR|vostFR)((\]|\)))?([ ._-])*)+                      # Subtitle Language and separator
     (par Fansub-Resistance)?                                                                  # Sentence for special fansub (Optionnal)
     (\[((v|V)(?P<version>[0-9]))\]([ ._-])*)?                                                 # Version and separator (Optional)
     ((\[(8|10)(Bits|bits|Bit|bit)\])?([ ._-])*)?                                              # Colour resolution and separator (Optional)
     ((\[|\()((FHD|HD|SD)*([ ._-])*((?P<extra_info>\d{3,4}[xp*]?\d{0,4}[\.\w\s-]*)))(\]|\)))?  # Source_Quality_Etc-
     ([ ._-]*\[(?P<crc>\w{8})\])?                                                              # CRC (Optional)
     .*                                                                                        # Separator and EOL
     """,
    ),
    (
        "anime_standard",
        # [Group Name] Show Name.13-14
        # [Group Name] Show Name - 13-14
        # Show Name 13-14
        # [Group Name] Show Name.13
        # [Group Name] Show Name - 13
        # Show Name 13
        r"""
     ^(\[(?P<release_group>.+?)\][ ._-]*)?                        # Release Group and separator
     (?P<series_name>.+?)[ ._-]+                                 # Show_Name and separator
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})                                       # E01
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?                             # E02
     (v(?P<version>[0-9]))?                                       # version
     [ ._-]+\[(?P<extra_info>\d{3,4}[xp]?\d{0,4}[\.\w\s-]*)\]       # Source_Quality_Etc-
     (\[(?P<crc>\w{8})\])?                                        # CRC
     .*?                                                          # Separator and EOL
     """,
    ),
    (
        "anime_standard_round",
        # [Stratos-Subs]_Infinite_Stratos_-_12_(1280x720_H.264_AAC)_[379759DB]
        # [ShinBunBu-Subs] Bleach - 02-03 (CX 1280x720 x264 AAC)
        r"""
     ^(\[(?P<release_group>.+?)\][ ._-]*)?                                    # Release Group and separator
     (?P<series_name>.+?)[ ._-]+                                              # Show_Name and separator
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})                                                   # E01
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?                                         # E02
     (v(?P<version>[0-9]))?                                                   # version
     [ ._-]+\((?P<extra_info>(CX[ ._-]?)?\d{3,4}[xp]?\d{0,4}[\.\w\s-]*)\)     # Source_Quality_Etc-
     (\[(?P<crc>\w{8})\])?                                                    # CRC
     .*?                                                                      # Separator and EOL
     """,
    ),
    (
        "anime_slash",
        # [SGKK] Bleach 312v1 [720p/MKV]
        r"""
     ^(\[(?P<release_group>.+?)\][ ._-]*)? # Release Group and separator
     (?P<series_name>.+?)[ ._-]+           # Show_Name and separator
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})                # E01
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?      # E02
     (v(?P<version>[0-9]))?                # version
     [ ._-]+\[(?P<extra_info>\d{3,4}p)     # Source_Quality_Etc-
     (\[(?P<crc>\w{8})\])?                 # CRC
     .*?                                   # Separator and EOL
     """,
    ),
    (
        "anime_standard_codec",
        # [Ayako]_Infinite_Stratos_-_IS_-_07_[H264][720p][EB7838FC]
        # [Ayako] Infinite Stratos - IS - 07v2 [H264][720p][44419534]
        # [Ayako-Shikkaku] Oniichan no Koto Nanka Zenzen Suki Janain Dakara ne - 10 [LQ][h264][720p] [8853B21C]
        r"""
     ^(\[(?P<release_group>.+?)\][ ._-]*)?                        # Release Group and separator
     (?P<series_name>.+?)[ ._]*                                   # Show_Name and separator
     ([ ._-]+-[ ._-]+[A-Z]+[ ._-]+)?[ ._-]+                       # funny stuff, this is sooo nuts ! this will kick me in the butt one day
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})                                       # E01
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?                             # E02
     (v(?P<version>[0-9]))?                                       # version
     ([ ._-](\[\w{1,2}\])?\[[a-z][.]?\w{2,4}\])?                        #codec
     [ ._-]*\[(?P<extra_info>(\d{3,4}[xp]?\d{0,4})?[\.\w\s-]*)\]    # Source_Quality_Etc-
     (\[(?P<crc>\w{8})\])?
     .*?                                                          # Separator and EOL
     """,
    ),
    (
        "anime_codec_crc",
        r"""
     ^(?:\[(?P<release_group>.*?)\][ ._-]*)?
     (?:(?P<series_name>.*?)[ ._-]*)?
     (?:(?P<ep_ab_num>(((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))[ ._-]*).+?
     (?:\[(?P<codec>.*?)\][ ._-]*)
     (?:\[(?P<crc>\w{8})\])?
     .*?
     """,
    ),
    (
        "anime SxEE",
        # Show_Name.1x02.Source_Quality_Etc-Group
        # Show Name - 1x02 - My Ep Name
        # Show_Name.1x02x03x04.Source_Quality_Etc-Group
        # Show Name - 1x02-03-04 - My Ep Name
        r"""
     ^((?!\[.+?\])(?P<series_name>.+?)[\[. _-]+)?  # Show_Name and separator if no brackets group
     (?P<season_num>\d+)x                          # 1x
     (?P<ep_num>\d+)                               # 02 and separator
     (([. _-]*x|-)                                 # linking x/- char
     (?P<extra_ep_num>
     (?!(1080|720|480)[pi])(?!(?<=x)26[45])           # ignore obviously wrong multi-eps
     \d+))*                                        # additional x03/etc
     [\]. _-]*((?P<extra_info>.+?)                 # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                          # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "anime_SxxExx",
        # Show.Name.S01E02.Source.Quality.Etc-Group
        # Show Name - S01E02 - My Ep Name
        # Show.Name.S01.E03.My.Ep.Name
        # Show.Name.S01E02E03.Source.Quality.Etc-Group
        # Show Name - S01E02-03 - My Ep Name
        # Show.Name.S01.E02.E03
        # Show Name - S01E02
        # Show Name - S01E02-03
        r"""
     ^((?P<series_name>.+?)[. _-]+)?             # Show_Name and separator
     (\()?s(?P<season_num>\d+)[. _-]*            # S01 and optional separator
     e(?P<ep_num>\d+)(\))?                       # E02 and separator
     (([. _-]*e|-)                               # linking e/- char
     (?P<extra_ep_num>(?!(1080|720|480)[pi])\d+)(\))?)*   # additional E03/etc
     ([. _-]+((?P<extra_info>.+?))?              # Source_Quality_Etc-
     ((?<![. _-])(?<!WEB)                        # Make sure this is really the release group
     -(?P<release_group>[^ -]+([. _-]\[.*\])?))?)?$              # Group
     """,
    ),
    (
        "anime_and_normal",
        # Bleach - s16e03-04 - 313-314
        # Bleach.s16e03-04.313-314
        # Bleach s16e03e04 313-314
        r"""
     ^(?P<series_name>.+?)[ ._-]+                 # start of string and series name and non optinal separator
     [sS](?P<season_num>\d+)[. _-]*               # S01 and optional separator
     [eE](?P<ep_num>\d+)                          # epipisode E02
     (([. _-]*e|-)                                # linking e/- char
     (?P<extra_ep_num>\d+))*                      # additional E03/etc
     ([ ._-]{2,}|[ ._]+)                          # if "-" is used to separate at least something else has to be there(->{2,}) "s16e03-04-313-314" would make sens any way
     ((?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?                       # absolute number
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?             # "-" as separator and anditional absolute number, all optinal
     (v(?P<version>[0-9]))?                       # the version e.g. "v2"
     .*?
     """,
    ),
    (
        "anime_and_normal_x",
        # Bleach - s16e03-04 - 313-314
        # Bleach.s16e03-04.313-314
        # Bleach s16e03e04 313-314
        r"""
     ^(?P<series_name>.+?)[ ._-]+                 # start of string and series name and non optinal separator
     (?P<season_num>\d+)[. _-]*               # S01 and optional separator
     [xX](?P<ep_num>\d+)                          # epipisode E02
     (([. _-]*e|-)                                # linking e/- char
     (?P<extra_ep_num>\d+))*                      # additional E03/etc
     ([ ._-]{2,}|[ ._]+)                          # if "-" is used to separate at least something else has to be there(->{2,}) "s16e03-04-313-314" would make sens any way
     ((?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?                       # absolute number
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?             # "-" as separator and anditional absolute number, all optinal
     (v(?P<version>[0-9]))?                       # the version e.g. "v2"
     .*?
     """,
    ),
    (
        "anime_and_normal_reverse",
        # Bleach - 313-314 - s16e03-04
        r"""
     ^(?P<series_name>.+?)[ ._-]+                 # start of string and series name and non optinal separator
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})                       # absolute number
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?             # "-" as separator and anditional absolute number, all optinal
     (v(?P<version>[0-9]))?                       # the version e.g. "v2"
     ([ ._-]{2,}|[ ._]+)                          # if "-" is used to separate at least something else has to be there(->{2,}) "s16e03-04-313-314" would make sens any way
     [sS](?P<season_num>\d+)[. _-]*               # S01 and optional separator
     [eE](?P<ep_num>\d+)                          # epipisode E02
     (([. _-]*e|-)                                # linking e/- char
     (?P<extra_ep_num>\d+))*                      # additional E03/etc
     .*?
     """,
    ),
    (
        "anime_and_normal_front",
        # 165.Naruto Shippuuden.s08e014
        r"""
     ^(?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})                       # start of string and absolute number
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?              # "-" as separator and anditional absolute number, all optinal
     (v(?P<version>[0-9]))?[ ._-]+                 # the version e.g. "v2"
     (?P<series_name>.+?)[ ._-]+
     [sS](?P<season_num>\d+)[. _-]*                 # S01 and optional separator
     [eE](?P<ep_num>\d+)
     (([. _-]*e|-)                               # linking e/- char
     (?P<extra_ep_num>\d+))*                      # additional E03/etc
     .*?
     """,
    ),
    (
        "anime_ep_name",
        r"""
     ^(?:\[(?P<release_group>.+?)\][ ._-]*)
     (?P<series_name>.+?)[ ._-]+
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?[ ._-]*?
     (?:v(?P<version>[0-9])[ ._-]+?)?
     (?:.+?[ ._-]+?)?
     \[(?P<extra_info>\w+)\][ ._-]?
     (?:\[(?P<crc>\w{8})\])?
     .*?
     """,
    ),
    (
        "anime_WarB3asT",
        # 003. Show Name - Ep Name.ext
        # 003-004. Show Name - Ep Name.ext
        r"""
     ^(?P<ep_ab_num>\d{3,4})(-(?P<extra_ab_ep_num>\d{3,4}))?\.\s+(?P<series_name>.+?)\s-\s.*
     """,
    ),
    (
        "anime_bare",
        # One Piece - 102
        # [ACX]_Wolf's_Spirit_001.mkv
        r"""
     ^(\[(?P<release_group>.+?)\][ ._-]*)?
     (?P<series_name>.+?)[ ._-]+                         # Show_Name and separator
     (?P<ep_ab_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4})            # E01
     (-(?P<extra_ab_ep_num>((?!(1080|720|480)[pi])|(?![hx].?26[45]))\d{1,4}))?  # E02
     (v(?P<version>[0-9]))?                                                  # v2
     .*?                                                                     # Separator and EOL
     """,
    ),
]
