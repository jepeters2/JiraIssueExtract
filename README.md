# JiraIssueExtract
This project is based on my need to provide a simple way to extract data from a JIRA instance to allow it to be imported into a BI tool. This uses the Jira Python client API's to put the results of a query into a serialized dictionary that can then be imported into Power BI or another tool. There is a configuration file that allows defining parameters including batch size, total results, execution of a JQL query and what fields to return.