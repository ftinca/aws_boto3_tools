### 1. check_asg_node_status.py
#####    a. Basic name filter example
```bash
python3 check_asg_node_status.py --profiles profile1 profile2 profile3 --regions us-east-1 us-west-2 us-east-2 ap-southeast-2 eu-central-1 --filters 'name=^nodes.*build$'
```
#####    b. Basic name usage filter example
```bash
python3 check_asg_node_status.py --profiles profile1 profile2 profile3 --regions us-east-1 us-west-2 us-east-2 ap-southeast-2 eu-central-1 --filters 'usage<50%'
```
#####    c. Both filters combined
```bash
python3 check_asg_node_status.py --profiles profile1 profile2 profile3 --regions us-east-1 us-west-2 us-east-2 ap-southeast-2 eu-central-1 --filters 'name=^nodes.*build$ and usage<50%'
```
