from sickchill import settings


class DelugeBase(object):
    @staticmethod
    def make_options(result):
        options = {}

        if settings.TORRENT_PATH or settings.TORRENT_PATH_INCOMPLETE:
            options.update(
                {
                    "download_location": settings.TORRENT_PATH_INCOMPLETE or settings.TORRENT_PATH,
                    "move_completed": bool(settings.TORRENT_PATH_INCOMPLETE),
                }
            )

        if settings.TORRENT_PATH and settings.TORRENT_PATH_INCOMPLETE:
            options.update({"move_completed": True, "move_completed_path": settings.TORRENT_PATH})

        if settings.TORRENT_PAUSED:
            options.update({"add_paused": True})

        # TODO: Figure out a nice way to do this. Will currently only work if there is only one file in the download.
        # file_priorities (list of int): The priority for files in torrent, range is [0..7] however
        # only [0, 1, 4, 7] are normally used and correspond to [Skip, Low, Normal, High]
        priority_map = {-1: [1], 0: [4], 1: [7]}

        # result.priority =  -1 = low, 0 = normal, 1 = high
        options.update({"file_priorities": priority_map[result.priority]})
        # options.update({'file_priorities': priority_map[result.priority] * num_files})

        if result.ratio:
            options.update({"stop_at_ratio": True})
            options.update({"stop_ratio": float(result.ratio)})
            # options.update({'remove_at_ratio': True})
            # options.update({'remove_ratio': float(result.ratio)})

        return options
