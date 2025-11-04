import argparse
from azureml.core import Workspace, LinkedService
from azureml.datadrift import DataDriftDetector
from azureml.core.authentication import InteractiveLoginAuthentication


def get_workspace_list(subscription_id: str, auth: InteractiveLoginAuthentication) -> dict[str, str]:
    ws_list = {}
    try:
        print(f"♻️ Retrieving workspaces for subscription {subscription_id}")
        ws_list = Workspace.list(subscription_id=subscription_id, auth=auth)
        for workspace_name, workspace in ws_list.items():
            ws_list[workspace_name] = workspace[0].resource_group
    except Exception as e:
        print(
            f"🚫Error retrieving workspaces for subscription {subscription_id}: {e}")
    return ws_list


def check_linked_services_usage(ws: Workspace):

    print(f"\t♻️ Checking linked services usage for workspace: {ws.name}...")
    linked_services = LinkedService.list(ws)
    if len(linked_services) == 0:
        print(f"\t✅ No linked services found for workspace: {ws.name}")
        return

    print(f"\t❌ Linked services found for workspace: {ws.name}")
    return


def check_datadrift_usage(ws: Workspace):
    print(f"\t♻️ Checking data drift usage for workspace: {ws.name} ...")
    try:
        datadrift_detectors = DataDriftDetector.list(ws)
        if len(datadrift_detectors) == 0:
            print(f"\t✅ No data drift usage found for workspace: {ws.name}")
            return

        print(f"\t❌ Data drift usage found for workspace: {ws.name}")
    except Exception as e:
        print(
            f"\t🚫 Could not retrieve data drift detectors for workspace {ws.name}: {e}")
    return


def main():
    parser = argparse.ArgumentParser(
        description="Azure ML Workspace Feature Usage Scanner")
    parser.add_argument("--subscription-id", type=str,
                        help="Azure subscription IDs to scan", nargs='+',)
    parser.add_argument("--tenant-id", type=str, help="Azure tenant ID")

    args = parser.parse_args()

    subscription_id_list = args.subscription_id
    tenant_id = args.tenant_id

    auth = InteractiveLoginAuthentication(tenant_id=tenant_id, force=True)

    for subscription_id in subscription_id_list:
        workspaces = get_workspace_list(subscription_id, auth=auth)
        print(
            f"Workspaces for subscription {subscription_id}: {workspaces.keys()}")

        for workspace_name, resource_group in workspaces.items():
            try:
                ws = Workspace(subscription_id=subscription_id,
                               resource_group=resource_group, workspace_name=workspace_name, auth=auth)

            except Exception as e:
                print(
                    f"🚫 Could not connect to workspace {workspace_name} from resource group {resource_group} in subscription {subscription_id}")
                print(f"Error: {e}")
                continue

            print(f"🟢 Connected to workspace: {ws.name}")

            check_linked_services_usage(ws)

            check_datadrift_usage(ws)


if __name__ == "__main__":
    main()
