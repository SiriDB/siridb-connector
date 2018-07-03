


class ImportCSV:

    def __init__(self, path):
        self.path = path

    def importCSV(self):
        csv_file = open(self.path, "r")
        headers = csv_file.readline()

        for header in headers:
            column_name = "{}".format(header)




        csv_file.close()

