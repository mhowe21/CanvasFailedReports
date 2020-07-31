import json
#attempt to install requests if not found attempt to install it via pip
try:
    import requests
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])



class userInputs():
    def __init__(self):
        self.token = None
        self.domain = None
        self.allAccounts = False

    def getToken(self):
        """Gets the users Canvas REST token."""
        self.token = input("Enter Your Canvas Token: ").strip()
        return self.token

    def getDomain(self):
        """Get the domain to run calls to."""
        self.domain = input("Enter your domain e.g (canvas.instructure.com): ").strip()
        return self.domain

    def runForSubAccounts(self):
        """Determin if all sub account reports should be scanned when running the script.
        Takes Y/N and returns a bool"""
        self.allAccounts = (
            input("Would you like to scan reports in all sub accounts [Y/N]: ")).lower()

        if(self.allAccounts == 'y' or self.allAccounts == 'yes'):
            self.allAccounts = True
        else:
            self.allAccounts = False

        return self.allAccounts


class apiData():
    def __init__(self, token, domain):
        self.token = token
        self.domain = domain
        self.jData = {}

    def getReportsJson(self, account="self"):
        """Run an API call to get a list of reports in canvas for that account level."""
        url = f"https://{self.domain}/api/v1/accounts/{account}/reports"

        payload = {'per_page': '100'}
        files = [

        ]
        headers = {'Authorization': f'Bearer {self.token}',
                   }

        response = requests.request(
            "GET", url, headers=headers, data=payload, files=files)
        self.jData = response.json()

        return self.jData

    def failedReports(self):
        """Return a list of reports that failed.
        Takes the jsonObject created when getReportsJson is called."""
        failedItems = []
        for item in self.jData:
            try:
                if(item["last_run"]["status"] == "error" or item["last_run"]["status"] == "failed"):
                    failedItems.append(item["report"])

            # we might not have a field for a never run report so we will skip over it.
            except TypeError:
                continue

        return(failedItems)

    def runningReports(self):
        """Return a list of reports that were currently still running when the program was executed.
        Takes the jsonObject created when getReportsJson is called"""
        runningItems = []
        for item in self.jData:
            try:
                if(item["last_run"]["status"] == "running"):
                    runningItems.append(item["last_run"]["report"])
            except TypeError:
                continue

        return(runningItems)

    def mapAccounts(self):
        """Return a list of all account IDs in an instance"""
        accountsList = []
        accountsList.append("self")

        url = f"https://{self.domain}/api/v1/accounts/self/sub_accounts"

        payload = {'per_page': '100',
                   'recursive': 'true'}
        files = []
        headers = {
            'Authorization': f'Bearer {self.token}',
        }

        response = requests.request(
            "GET", url, headers=headers, data=payload, files=files)

        accountJData = response.json()
        for items in accountJData:
            accountsList.append(items["id"])

        return accountsList


def main():
    userIn = userInputs()
    token = userIn.getToken()
    domain = userIn.getDomain()
    sub = userIn.runForSubAccounts()

    CanvasAPI = apiData(token, domain)

    # clean this up later running 1 for the account self and then the rest if true.

    if(sub == False):
        print("Running...")
        CanvasAPI.getReportsJson()
        if(len(CanvasAPI.failedReports()) > 0):
            print(
                f"the following reports {CanvasAPI.failedReports()} gave an error in the root account")
        if(len(CanvasAPI.runningReports()) > 0):
            print(
                f"the following reports {CanvasAPI.runningReports()} are still running in the root account")
    elif(sub == True):
        print("Running...")
        accountList = CanvasAPI.mapAccounts()
        for accountNumber in accountList:
            CanvasAPI.getReportsJson(accountNumber)
            if(len(CanvasAPI.failedReports()) > 0):
                print(
                    f"the following reports failed {CanvasAPI.failedReports()} for account {accountNumber}")
            if(len(CanvasAPI.runningReports()) > 0):
                print(
                    f"the following reports are still running {CanvasAPI.runningReports()} for account {accountNumber}")
        print("done!")


if __name__ == "__main__":
    main()
