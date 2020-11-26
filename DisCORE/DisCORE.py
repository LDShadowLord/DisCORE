class Logs:
    def __init__(self, url):
        """
        Create a Discord Logs Item
        The 'url' argument is for a Discord "logs" channel
        """
        import dhooks

        self.version = "0.5.1"

        self.url = url
        self.hook = dhooks.Webhook(url)
        self.log_output = []
        self.debug = False

    def debug(self, state=None):
        """
        Toggles Debug Mode - Prevents unnecessary printing
        Returns the debug state when called.
        The 'state' argument can change the Debug State.
        """

        if state != None:
            if state == True:
                self.debug = True
            else:
                self.debug = False

        return self.debug
        
    def print(self, content, debug=False):
        """
        Print contents to screen and to Discord
        The 'debug' argument can be used to prevent printing
        """

        if debug != self.debug:
            pass
        else:
            content = str(content)
            print(content)
            self.log_output.append(content)
        
    def commit(self, clear=True):
        """
        Commit logs to Discord
        The 'clear' argument empties the previous logs upon commit
        """
        ready_to_output = "Generated by DisCORE 𝖑𝖔𝖌𝖘 "+self.version+"\n\n"
        for line in self.log_output:
            if len(line)+len(ready_to_output) > 1950:
                self.hook.send(content="```"+ready_to_output+"```")
                ready_to_output = "" + line + "\n"

            else:
                ready_to_output = ready_to_output + line + "\n"

        self.hook.send(content="```"+ready_to_output+"```")    
        if clear:
            self.log_output = []

class Notify:
    def __init__(self, url, debug=False):
        """
        Create a Discord Notify Item
        The 'url' argument is for the Discord "notification" channel
        The 'debug' argument is to test code without spamming Discord
        """
        import dhooks

        self.version = "0.5.2"

        self._embedBase = dhooks.Embed
        self.url = url.replace("discordapp.com","discord.com")
        self._hook = dhooks.Webhook(url)
        self.debug = debug

    def author(self):
        """
        Returns an example dictionary formatted for use with the embed function.
        Use this dictionary to add an author to an embed
        """
        authorDict = {
            "name":"",
            "icon":"",
            "url":""
        }
        return authorDict

    def embed(self, description, title, url=None, color=0x7289da, thumbnail=None, image=None, author=None, removeFooter=False):
        """
        Create a Discord Embed
        The 'description' argument is for the main text of the embed
        The 'title' argument is for the bolded, linkable, text of the embed
        The 'url' argument is for the target of the title link
        The 'color' argument is for the embed edge colour
        The 'thumbnail' argument is for the image URL of the thumbnail
        The 'image' argument is for the image URL of the main image
        The 'author' argument is for a dictionary of author arguments
        """
        if url == None:
            exportEmbed = self._embedBase(
                description = description,
                title = title,
                color = color
            )
        else:
            exportEmbed = self._embedBase(
                description = description,
                title = title,
                color = color,
                url = url
            )

        if thumbnail != None:
            exportEmbed.set_thumbnail(thumbnail)

        if image != None:
            exportEmbed.set_image(image)

        if author != None:
            exportEmbed.set_author(author["name"],author["icon"],author["url"])

        if removeFooter != True:
            exportEmbed.set_footer("Generated by DisCORE ｎｏｔｉｆｙ "+self.version, "https://raw.githubusercontent.com/LDShadowLord/DisCORE/master/DisCORE/assets/logo.png")
        
        return exportEmbed
            

    def notify(self, embed, catch=False):
        """
        Create a Discord Notification
        The 'embed' argument is an embed object
        The 'catch' argument catches any errors when notifying without crashing the script
        """
        if catch != True:
            self._hook.send(embed=embed)
            return True
        else:
            try:
                self._hook.send(embed=embed)
                return True
            except:
                return False

class Data_JSON:
    def __init__(self, object=None, file=None):
        """
        Create a DisCORE Data JSON Item
        The 'object' argument is the JSON object that is to be serialized
        The 'file' argument is a file path for either importing or exporting JSON to file
        """
        import json

        if object == None and file == None:
            raise ValueError("Both cannot be None!")
        self.object = object
        self.file = file

    def dump(self):
        """
        Return a dictionary as a JSON object
        """
        
        if self.file != None:
            pass
        
        elif self.file == None:
            output = json.dumps(self.object)
            return output

    def load(self):
        """
        Return a dictionary from a JSON object
        """
        
        if file != None:
            pass
        
        elif file == None:
            output = json.loads(self.object)
            return output

class Data_SQL:
    def __init__(self, details):
        """
        Create a DisCORE Data SQL Item
        The 'details' argument is for a tuple containing:
        host, database, username, password
        In that order.
        """
        import mysql.connector

        self.column_index = 3

        self.db = mysql.connector.connect(
            host = details[0],
            database = details[1],
            user = details[2],
            password = details[3]
            )

        self.cursor = self.db.cursor()

    def execute(self, query, fetch="all"):
        """
        Execute an Arbitrary SQL query
        The 'query' argument is the SQL to execute
        The 'fetch' argument decides what is returned. Acceptable answers are "all" or "one"
        """
        self.cursor.execute(query)

        if fetch=="all":
            return self.cursor.fetchall()
        elif fetch=="one":
            return self.cursor.fetchone()

    def execute_safely(self, query, insertion, fetch="all"):
        """
        Execute an Arbitrary SQL query with protections
        The 'query' argument is the SQL to execute
        The 'insertion' argument inserts user-provided data where %s to limit potential for SQL injection.
        The 'fetch' argument decides what is returned. Acceptable answers are "all" or "one"
        NOTE: This doesn't seem to work properly for table names, it can only be used for value insertion
        """
        self.cursor.execute(query, insertion)

        if fetch=="all":
            return self.cursor.fetchall()
        elif fetch=="one":
            return self.cursor.fetchone()

    def get_column_names(self, table):
        """
        Retrieve the names of columns of a particular table
        The 'table' argument is name of the target table
        NOTE: This is designed to work on MariaDB, the default behaviour can be overwritten
        NOTE: by modifying 'column_index'
        """
        result = self.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'{table_name}'".format(table_name=table))
        output = []

        for item in result:
            output.append(item[self.column_index])

        return output

    def return_dictionary(self, table, query, primary=0, is_json=False):
        """
        Perform a query against a table and format it as a dictionary.
        The 'table' argument is the name of the target table
        The 'query' argument is the target query
        The 'primary' argument is the index of the primary key
        The 'is_json' argument returns the object as JSON formatted
        """
        columns = self.get_column_names(table)
        returned_data = self.execute(query)

        output = {}
        data_length = len(returned_data[0])
        required_indices = []
        for i, blank in enumerate(returned_data[0], 0):
            required_indices.append(i)

        required_indices.remove(primary)

        for item in returned_data:
            temp_output = {}
            for item_2 in required_indices:
                temp_output[columns[item_2]] = item[item_2]

            output[item[primary]] = temp_output

        if is_json == True:
            my_json = Data_JSON(object=output)
            output = my_json.dump()

        return output

    def commit_dictionary(self, object, table, primary=0, is_json=False):
        """
        Provide a formatted dictionary and commit to a database
        The 'object' argument is a dictionary or JSON Object
        The 'table' argument is the name of the target table
        The 'primary' argument is the index of the primary key
        The 'is_json' argument returns the object as JSON formatted
        """

        #Get the column names from the database, as well as the length.
        #Then convert the column tuple to a string to be injected into the query
        columns = self.get_column_names(table)
        column_length = len(columns)
        column_index = columns
        columns = str(columns).replace("[","(").replace("]",")").replace("'","")

        #Begin Crafting additional injections by enumerating over the columns
        #This guarantees that the variable should always have the correct amount of variables in
        #ValueSubs is the %s injection
        #ValueList will contain the actual variables to be injected
        value_substitution = "("
        blank_value_list = []
        update_substitution = ""
        for i, blank in enumerate(column_index, 0):
            value_substitution += "%s"
            if i != len(column_index)-1:
                value_substitution += ", "

            blank_value_list.append("")

            if i == primary:
                pass
            else:
                update_substitution += column_index[i]+"=VALUES("+column_index[i]+")"
                if i != len(column_index)-1:
                    update_substitution += ", "

        value_substitution += ")"


        #Begin iterating over the provided dictionary
        sub_values = []
        for item in object:
            value_list = blank_value_list

            value_list[primary] = item
            for name in column_index:
                if name == column_index[primary]:
                    pass
                else:
                    value_list[column_index.index(name)] = object[item][name]
 
            sub_values.append(tuple(value_list))

        query = """INSERT INTO {table_name} {column_name}
                   VALUES {value_substitution}
                   ON DUPLICATE KEY UPDATE {update_substitution};""".format(
                   table_name=table,
                   column_name=columns,
                   value_substitution=value_substitution,
                   update_substitution=update_substitution
                )

        #print(query)
        #print(value_substitution)
        #print(sub_values)
        #print(query.replace(value_substitution, str(sub_values[0])))
        self.cursor.executemany(query, sub_values)

        self.db.commit()
        return (self.cursor.rowcount, "was inserted.")