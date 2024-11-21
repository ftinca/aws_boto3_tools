import boto3
import concurrent.futures
import argparse
import re

def get_asgs_for_region(profile, region, filter):
    print(f"* Fetching Auto Scaling Groups for {profile} region {region}      ", end="\r")
    session = boto3.Session(profile_name=profile, region_name=region)
    client = session.client('autoscaling')
    asgs = []
    paginator = client.get_paginator('describe_auto_scaling_groups')
    if filter:
        asgs = [{'AutoScalingGroupName': asg['AutoScalingGroupName'], 'DesiredCapacity': asg['DesiredCapacity'], 'MaxSize': asg['MaxSize']} for page in paginator.paginate() for asg in page['AutoScalingGroups'] if re.search(filter, asg['AutoScalingGroupName'])]
    else:
        asgs = [{'AutoScalingGroupName': asg['AutoScalingGroupName'], 'DesiredCapacity': asg['DesiredCapacity'], 'MaxSize': asg['MaxSize']} for page in paginator.paginate() for asg in page['AutoScalingGroups']]
    print(f" "*100, end="\r")
    return {'region': region, 'asgs': asgs}


def get_asgs_by_profile(profile_name, regions, input_filter):
    print(f"* Started worker thread for {profile_name}      ", end="\r")
    current_profile_asgs = {'profile': profile_name}
    region_asgs = []
    with concurrent.futures.ThreadPoolExecutor(4) as executor:
        future_asgs = {executor.submit(get_asgs_for_region, profile_name, region, input_filter): region for region in regions}
        region_asgs = [future.result() for future in concurrent.futures.as_completed(future_asgs)]
    current_profile_asgs['regions'] = region_asgs
    print_results(current_profile_asgs)


def get_vars_by_capacity(desired, maximum):
    capacity = calculate_percentage(desired, maximum)
    red = "\033[31m"
    yellow = "\033[33m"
    green = "\033[32m"
    end_colour = "\033[m"
    warning = '\u26A0'
    yellow_warning = f'{yellow}{warning}{end_colour}'
    red_warning = f'{red}{warning}{end_colour}'
    green_check = f'{green}{"\u2713"}{end_colour}'
    if desired >= 0.9 * maximum:
        return {'colour': red, 'sign':red_warning, 'capacity': capacity} # Red
    elif desired < 0.8 * maximum:
        return {'colour': green, 'sign': green_check, 'capacity': capacity}  # Green
    elif 0.8 * maximum <= desired < 0.95 * maximum:
        return {'colour': yellow, 'sign': yellow_warning, 'capacity': capacity} # Yellow


def calculate_percentage(desired, maximum):
    if maximum == 0:  # Prevent division by zero
        return "Undefined (division by zero)"
    percentage = (desired / maximum) * 100
    return percentage

def print_results(result):
    if result:
        print(f"\n{result['profile']}")
        for region in result['regions']:
            if region['asgs']:
                cyan = "\033[36m"
                end_clr = "\033[m"
                right_arrow = "\u2192" 
                print(f"{right_arrow} {cyan}{region['region']}{end_clr}")
                for asg in region['asgs']:
                    maximum_capacity = asg['MaxSize']
                    desired_capacity = asg['DesiredCapacity']
                    vars = get_vars_by_capacity(desired_capacity, maximum_capacity)
                    if vars:
                        end_clr = "\033[m"
                        bullet = '\u00B7'
                        print(f"  {vars.get('sign')} Auto Scaling Group: {asg['AutoScalingGroupName']}")
                        print(f"  {bullet} Current Capacity: {asg['DesiredCapacity']:>10}")
                        print(f"  {bullet} Maximum Capacity: {asg['MaxSize']:>10}")
                        print(f"  {bullet} Capacity %: {vars.get('colour')}{int(vars.get('capacity')):>16}%{end_clr}")

def main(profiles, regions, filter=None):
    with concurrent.futures.ThreadPoolExecutor(5) as executor:
        {executor.submit(get_asgs_by_profile, profile, regions, filter): profile for profile in profiles if profile}

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Check Auto Scaling Group node status. Make sure you are logged in AWS before running this.")
        parser.add_argument("--profiles" , '-p', nargs='+', help="AWS profile to use. You can specify multiple profiles separated by spaces. If not specified, all profiles will be checked.", required=True)
        parser.add_argument("--regions", '-r', nargs='+', help="AWS regions to check. You can specify multiple regions separated by spaces. If not specified, all regions will be checked.", required=True)
        parser.add_argument("--filters", '-f', help="Regex - print only ASGs that contain the filter value in their name.", type=str)
        args = parser.parse_args()
        filter = args.filters
        profiles = args.profiles
        regions = args.regions
        main(profiles, regions, filter)
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
