⚠️ **DISCLAIMER:**  
This script is provided "AS IS" without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the author or contributors be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the script or the use or other dealings in the script. Use at your own risk.

# Description
This project intends to provide a script to be executed by an Admin that has full access to the subscription and Azure Machine Learning workspaces, in order to scan for the usage of the following features that will be deprecated:

- Add linked services
- Monitor data drift
- Use v2 data asset with labeling **(not implemented yet!!!)**

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

