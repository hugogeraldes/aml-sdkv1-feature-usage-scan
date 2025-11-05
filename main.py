import argparse
import urllib.request
import json
import logging
from azureml.core import Workspace, LinkedService
from azureml.datadrift import DataDriftDetector
from azureml.core.authentication import InteractiveLoginAuthentication
from msrest.exceptions import HttpOperationError

# supressing datadrift package logging messages
logger = logging.getLogger(
    "azureml.datadrift._logging._telemetry_logger.datadriftdetector.list")
logger.disabled = True


# def get_workspace_list(subscription_id: str, auth: InteractiveLoginAuthentication) -> dict[str, str]:
#    """
#    Retrieve all Azure Machine Learning workspaces within a given subscription.
#
#    This function connects to Azure using the provided authentication and lists all
#    available ML workspaces in the specified subscription. It returns a mapping of
#    workspace names to their corresponding resource group names.
#
#    Args:
#        subscription_id (str): The Azure subscription ID to scan for workspaces
#        auth (InteractiveLoginAuthentication): Azure authentication object with proper credentials
#
#    Returns:
#        dict[str, str]: Dictionary mapping workspace names to resource group names.
#                       Returns empty dict if no workspaces found or on error.
#
#    Raises:
#        Catches all exceptions internally and prints error messages to console.
#    """
#    ws_list = {}
#    try:
#        print(f"♻️ Retrieving workspaces for subscription {subscription_id}")
#        ws_list = Workspace.list(subscription_id=subscription_id, auth=auth)
#        for workspace_name, workspace in ws_list.items():
#            ws_list[workspace_name] = workspace[0].resource_group
#    except Exception as e:
#        print(
#            f"🚫Error retrieving workspaces for subscription {subscription_id}: {e}")
#    return ws_list


def check_linked_services_usage(ws: Workspace):
    """
    Check if the Azure ML workspace is using linked services (deprecated feature).

    Linked services are a deprecated feature in Azure ML that allowed connections
    to external services. This function scans the workspace to detect if any
    linked services are configured, which indicates usage of deprecated functionality.

    Args:
        ws (Workspace): Azure ML Workspace object to scan for linked services

    Returns:
        None: Function prints results directly to console with status indicators:
              ✅ for no usage found (good)
              ❌ for deprecated feature usage found (needs attention)
    """

    print(f"\t♻️ Checking linked services usage for workspace: {ws.name}...")
    linked_services = LinkedService.list(ws)
    if len(linked_services) == 0:
        print(f"\t✅ No linked services found for workspace: {ws.name}")
        return

    print(f"\t❌ Linked services found for workspace: {ws.name}")
    return


def check_datadrift_usage(ws: Workspace):
    """
    Check if the Azure ML workspace is using data drift monitoring (deprecated feature).

    Data drift monitoring is a deprecated feature in Azure ML SDK v1 that tracked
    changes in data distribution over time. This function scans the workspace for
    any configured data drift detectors to identify usage of this deprecated functionality.

    Args:
        ws (Workspace): Azure ML Workspace object to scan for data drift detectors

    Returns:
        None: Function prints results directly to console with status indicators:
              ✅ for no usage found (good)  
              ❌ for deprecated feature usage found (needs attention)
              🚫 for errors during scanning

    Note:
        HTTP 404 errors are treated as "no usage found" since they indicate
        the data drift service is not available/configured for the workspace.
    """
    print(f"\t♻️ Checking data drift usage for workspace: {ws.name} ...")
    try:
        datadrift_detectors = DataDriftDetector.list(ws)
        if len(datadrift_detectors) == 0:
            print(f"\t✅ No data drift usage found for workspace: {ws.name}")
            return

        print(f"\t❌ Data drift usage found for workspace: {ws.name}")

    except HttpOperationError as http_err:
        if http_err.response.status_code == 404:
            print(f"\t✅ No data drift usage found for workspace: {ws.name}")
            return
        else:
            print(
                f"\t🚫 Could not retrieve data drift detectors for workspace {ws.name}: {http_err}")
            return
    except Exception as e:
        print(
            f"\t🚫 Could not retrieve data drift detectors for workspace {ws.name}: {e}")
    return


def get_labeling_projects(sub_id: str, rg: str, workspace: str, ws_region: str, token: str) -> list[dict[str, str]] | None:
    """
    Retrieve all data labeling projects from an Azure ML workspace via REST API.

    This function calls the Azure ML labeling API to fetch a list of all labeling
    projects in the specified workspace. It handles pagination automatically to
    ensure all projects are retrieved, even if they span multiple pages of results.

    Args:
        sub_id (str): Azure subscription ID where the workspace is located
        rg (str): Resource group name containing the workspace
        workspace (str): Name of the Azure ML workspace to scan
        ws_region (str): Azure region where the workspace is located (e.g., 'eastus')
        token (str): Bearer authentication token for API access

    Returns:
        list[dict]: List of project dictionaries, each containing 'id' and 'name' keys.
                   Returns empty list if no projects found.
                   Returns None if API call fails or encounters errors.

    Note:
        The function automatically handles paginated responses using the 'nextLink'
        property to retrieve all projects across multiple API pages.
    """

    projects = []

    url = (f"https://ml.azure.com/api/{ws_region}"
           f"/labeling-api/v1.0"
           f"/subscriptions/{sub_id}"
           f"/resourceGroups/{rg}"
           f"/providers/Microsoft.MachineLearningServices/workspaces/{workspace}"
           f"/projects/summaries?pageSize=25&searchText=&orderBy=createdTime&orderByAsc=false")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    request = urllib.request.Request(url, headers=headers, method="GET")
    response = None
    try:
        with urllib.request.urlopen(request) as response:
            response = json.loads(response.read().decode())
            # print(response)

    except Exception as e:
        print(f"Error fetching labeling summaries: {e}")
        return None

    if len(response["value"]) < 1:
        return []

    for project in response["value"]:
        projects.append({"id": project["id"], "name": project["name"]})

    # in the odd chance we get multiple pages, we will need to iterate through them
    while "nextLink" in response:
        next_url = response["nextLink"]
        request = urllib.request.Request(
            next_url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(request) as response:
                response = json.loads(response.read().decode())
                print(response)

        except Exception as e:
            print(f"Error fetching labeling summaries: {e}")
            return None

        for project in response["value"]:
            projects.append({"id": project["id"], "name": project["name"]})

    return projects


def get_project_details(sub_id: str, rg: str, workspace: str, ws_region: str, token: str, project_id: str) -> dict[str, str] | None:
    """
    Retrieve detailed information for a specific data labeling project.

    This function fetches detailed metadata for a specific labeling project,
    including the dataset information needed to determine if the project is
    using deprecated v2 data assets instead of the supported FileDataset format.

    Args:
        sub_id (str): Azure subscription ID where the workspace is located
        rg (str): Resource group name containing the workspace  
        workspace (str): Name of the Azure ML workspace containing the project
        ws_region (str): Azure region where the workspace is located (e.g., 'eastus')
        token (str): Bearer authentication token for API access
        project_id (str): Unique identifier of the labeling project to examine

    Returns:
        dict: Project details containing 'datasetId' and 'datasetType' keys.
              The 'datasetType' indicates whether it's using deprecated v2 assets.
              Returns None if API call fails or encounters errors.

    Note:
        Function prints project details to console for debugging purposes.
        The 'datasetType' field is critical for detecting v2 data asset usage.
    """
    project_details = {}
    url = (f"https://ml.azure.com/api/{ws_region}"
           f"/labeling-api/v1.0/subscriptions/{sub_id}"
           f"/resourceGroups/{rg}"
           f"/providers/Microsoft.MachineLearningServices/workspaces/{workspace}"
           f"/projects/{project_id}")

    headers = {"Authorization": f"Bearer {token}"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    response = None
    try:
        with urllib.request.urlopen(request) as response:
            response = json.loads(response.read().decode())
            # print(response)

    except Exception as e:
        print(f"Error fetching project details: {e}")
        return None

    project_details["datasetId"] = response["datasetId"]
    project_details["datasetType"] = response["datasetType"]

    print(project_details)

    return project_details


def check_v2_dataset_usage(sub_id: str, rg: str, workspace: str, ws_region: str, token: str):
    """
    Check if labeling projects in the workspace are using v2 data assets (deprecated feature).

    This function scans all labeling projects in the workspace to detect usage of
    v2 data assets, which are deprecated in favor of FileDataset format. It examines
    each project's dataset type to identify potential migration needs.

    Args:
        sub_id (str): Azure subscription ID where the workspace is located
        rg (str): Resource group name containing the workspace
        workspace (str): Name of the Azure ML workspace to scan
        ws_region (str): Azure region where the workspace is located (e.g., 'eastus')
        token (str): Bearer authentication token for API access

    Returns:
        None: Function prints results directly to console with status indicators:
              ✅ for no deprecated usage found (good)
              ❌ for deprecated v2 data asset usage found (needs attention) 
              🚫 for errors during scanning

    Note:
        Function stops at the first project found using v2 data assets and reports it.
        Projects using "FileDataset" format are considered compliant (not deprecated).
    """
    print(
        f"\t♻️ Checking for v2 data asset usage in labeling projects: {workspace} ...")

    projects = get_labeling_projects(sub_id, rg, workspace, ws_region, token)
    if projects is None:
        print("\t🚫 Could not retrieve labeling projects.")
        return

    for project in projects:
        details = get_project_details(
            sub_id, rg, workspace, ws_region, token, project["id"])

        if details["datasetType"] != "FileDataset":
            print(f"\t❌ Project {project['name']} is using a v2 data asset")
            return

    print(f"\t✅ No v2 dataset usage found for labeling projects")

    return


def get_workspace_list(subscription_id: str, token: str) -> list[dict]:
    """Utility function to retrieve a list of workspaces in the Azure subscription.
    uses REST API for Microsoft Graph to check the workspace type.

    Args:
        subscription_id (str): Azure subscription ID to retrieve workspaces from
        token (str): Bearer authentication token for API access
    Returns:
        list[dict]: List of valid workspaces in the specified subscription.
    """
    workspace_list = []

    url = "https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    query = {
        "subscriptions": [f"{subscription_id}"],
        "query": """Resources 
              | where type == \"microsoft.machinelearningservices/workspaces\" 
               and kind == \"Default\"
              | project subscriptionId,resourceGroup,name,location
            """
    }

    request = urllib.request.Request(
        url, headers=headers, method="POST", data=json.dumps(query).encode('utf-8'))
    response = None
    try:
        with urllib.request.urlopen(request) as response:
            response = json.loads(response.read().decode())

    except Exception as e:
        print(f"Error fetching workspace list: {e}")
        return []

    return response["data"]


def main():
    """
    Main entry point for the Azure ML Workspace Feature Usage Scanner.

    This script scans Azure Machine Learning workspaces across specified subscriptions
    to detect usage of deprecated SDK v1 features that will be retired. It checks for:

    1. Linked Services - Deprecated service connection mechanism
    2. Data Drift Monitoring - Deprecated drift detection functionality  
    3. v2 Data Assets in Labeling Projects - Deprecated dataset format

    The scanner requires administrator access to all target subscriptions and workspaces
    to perform comprehensive feature usage analysis.

    Command Line Arguments:
        --tenant-id: Azure AD tenant ID for authentication
        --subscription-id: One or more Azure subscription IDs to scan (space-separated)

    Usage Examples:
        # Single subscription
        python main.py --tenant-id <tenant-id> --subscription-id <sub-id>

        # Multiple subscriptions  
        python main.py --tenant-id <tenant-id> --subscription-id <sub1> <sub2> <sub3>

    Output:
        Console output with emoji indicators:
        🟢 - Successful connections
        ✅ - No deprecated features found (good)
        ❌ - Deprecated features detected (needs attention)
        🚫 - Errors or access issues
        ♻️ - Scanning progress indicators
    """
    parser = argparse.ArgumentParser(
        description="Azure ML Workspace Feature Usage Scanner")
    parser.add_argument("--subscription-id", type=str,
                        help="Azure subscription IDs to scan", nargs="+",)
    parser.add_argument("--tenant-id", type=str, help="Azure tenant ID")

    args = parser.parse_args()

    subscription_id_list = args.subscription_id
    tenant_id = args.tenant_id

    auth = InteractiveLoginAuthentication(tenant_id=tenant_id, force=True)
    token = auth.get_token().token

    for subscription_id in subscription_id_list:
        workspaces = get_workspace_list(subscription_id, token)
        print(
            f"Workspaces for subscription {subscription_id}: {[workspace['name'] for workspace in workspaces]}")

        # for workspace_name, resource_group in workspaces.items():
        #    try:
        #        ws = Workspace(subscription_id=subscription_id,
        #                       resource_group=resource_group, workspace_name=workspace_name, auth=auth)

        for workspace in workspaces:
            try:
                ws = Workspace(subscription_id=workspace['subscriptionId'],
                               resource_group=workspace['resourceGroup'],
                               workspace_name=workspace['name'], auth=auth)

            except Exception as e:
                print(
                    f"🚫 Could not connect to workspace {workspace['name']} from resource group {workspace['resourceGroup']} in subscription {subscription_id}")
                print(f"Error: {e}")
                continue

            print(f"🟢 Connected to workspace: {ws.name}")

            check_linked_services_usage(ws)

            check_datadrift_usage(ws)

            check_v2_dataset_usage(ws.subscription_id, ws.resource_group, ws.name,
                                   ws.location, token)


if __name__ == "__main__":
    main()
