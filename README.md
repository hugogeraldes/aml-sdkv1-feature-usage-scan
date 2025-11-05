⚠️ **DISCLAIMER:**  
This script is provided "AS IS" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the author or contributors be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the script or the use or other dealings in the script. Use at your own risk.

# Description
This project intends to provide a script to be executed by an Admin that has full access to the subscription and Azure Machine Learning workspaces, in order to scan for the usage of the following features that will be deprecated:

- Add linked services
- Monitor data drift
- Use v2 data asset with labeling

# Prerequisites
This project depends on the "uv" utility to be installed on the machine where it's going to be executed.  
["uv" install instructions for Windows](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_2)  
["uv" install instructions for Linux and MacOs](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1)

The user running the tool will need to have Contributor access on all workspaces.

# How to use:
1) Clone the repository
```
git clone https://github.com/hugogeraldes/aml-sdkv1-feature-usage-scan.git

```
2) Navigate to the project's folder.
```
cd aml-sdkv1-feature-usage-scan

```
3) Use "uv" to recreate the project's Python virtual environment
```
uv sync

```

4) Execute the tool by passing the Tenant ID and Subscription IDs:

```

uv run main.py --tenant-id <your tenant id> --subscription-id <subscription id 1> <subscription id 2>

```
Examples:

```
# Single subscription
uv run main.py --tenant-id f3c71bdb-8cab-45b6-a35e-6875668a9abf --subscription-id 39a7d307-95da-4d5c-9c2e-5d1fdbefdc53

# Multiple subscriptions
uv run main.py --tenant-id f3c71bdb-8cab-45b6-a35e-6875668a9abf --subscription-id 39a7d307-95da-4d5c-9c2e-5d1fdbefdc53 ea4abf82-c7c8-4e24-b40c-c80f2d24b443 a16cc889-e660-478a-b626-1a7d78c86f35

```
# How to obtain the list of subscriptions that need to be checked for a given tenant?
1) An admin should go to Azure Portal and go to the Azure Resource Graph  
![Screenshot of Azure Portal search bar showing the query "Resource graph explorer". The dropdown displays categories: "All" (selected), "Services (22)", "Documentation (99+)", and "More (4)". Under Services, the first result is "Resource graph explorer" with an icon and label "Resource Manager".](/images/search_graph.png)
2) Make sure to select the scope to the tenant
![Screenshot of Azure Portal showing Resource Graph Explorer. The left navigation menu includes options like Resource Manager, All resources, Tags, and Resource graph explorer highlighted. The main panel displays a new query named "New query 1" with scope set to Directory and a link to Select scope. Below, categories such as General, AI + machine learning, Analytics, Compute, Containers, and Databases are listed.](/images/check_scope.png)
3) Execute the folwing query:
```kql
resources
| where type=="microsoft.machinelearningservices/workspaces" and kind == "Default"
| distinct subscriptionId
```
![Screenshot of Azure Resource Graph Explorer query editor. The query shown selects resources where type equals "microsoft.machinelearningservices/workspaces" and kind equals "Default", then returns distinct subscriptionId. A blue Run button is highlighted in the top left, next to Save and Share options.](/images/execute_query.png)

# How to interpret the results:
♻️ - Will be shown to indicate an operation is ongoing.  
🟢 - Will be shown uppon sucessful connection to a workspace.  
🚫 - Will be shown when it is not possible to connect to a workspace or to complete the assessment for the usage of a given feature.  
❌ - Will be shown when a deprecated feature is in use.  
✅ - Will be shown when it was detected that a deprecated feature is not being used.  


