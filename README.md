**How to add exceptions**

1. Check TVDB
    * get the TVDB ID of the show
    * search for any similar shows that could conflict, note them

2. Check NewzNab provider
    * find all scene names of the correct show
    * find any shows which may conflict because of similar names

3. Fixup scene names from step 2
    * for each scene name turn it back into a show name. This means adding back parentheses, apostrophes, ampersands, colons, exclamation marks, and question marks.
eg. Shows.Name.2010 -> Show's Name! (2010) (since SB will turn that back into Shows.Name.2010)

Remember that this list appends the TVDB name, thus there is no need to include it.

Exceptions should be of the format:

      tvdb_id: 'Name 1', 'Name 2', ..., 'Name N'

Apostrophes inside the show name should be escaped with a backslash ('Show\'s Name').
