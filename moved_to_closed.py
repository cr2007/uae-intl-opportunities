#!/usr/bin/env python3
"""
Helper script to move closed opportunities from data.json to closed_opportunities.json

Usage:
    python move_to_closed.py --category "Competitions" --name "FemTech Hackathon"
    
Or run interactively:
    python move_to_closed.py
"""

import json
import argparse
from datetime import datetime


def load_data():
    """Load both active and closed opportunities"""
    with open('data.json', 'r', encoding='utf-8') as f:
        active_data = json.load(f)
    
    try:
        with open('closed_opportunities.json', 'r', encoding='utf-8') as f:
            closed_data = json.load(f)
    except FileNotFoundError:
        closed_data = []
    
    return active_data, closed_data


def save_data(active_data, closed_data):
    """Save both files"""
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(active_data, f, indent=2, ensure_ascii=False)
    
    with open('closed_opportunities.json', 'w', encoding='utf-8') as f:
        json.dump(closed_data, f, indent=2, ensure_ascii=False)


def find_opportunity(active_data, category, name):
    """Find an opportunity in the active data"""
    
    # Check closingSoon
    if 'closingSoon' in active_data:
        for i, opp in enumerate(active_data['closingSoon']):
            if opp['name'] == name:
                return 'closingSoon', i, opp
    
    # Check categories
    if 'categories' in active_data and category in active_data['categories']:
        for i, opp in enumerate(active_data['categories'][category]):
            if opp['name'] == name:
                return category, i, opp
    
    return None, None, None


def move_to_closed(active_data, closed_data, category, name, closed_date=None):
    """Move an opportunity from active to closed"""
    
    cat_key, index, opportunity = find_opportunity(active_data, category, name)
    
    if opportunity is None:
        print(f"❌ Opportunity '{name}' not found in category '{category}'")
        return False
    
    # Add metadata
    opportunity['category'] = category
    opportunity['closedDate'] = closed_date or datetime.now().strftime('%Y-%m-%d')
    
    # Remove from active
    if cat_key == 'closingSoon':
        active_data['closingSoon'].pop(index)
    else:
        active_data['categories'][cat_key].pop(index)
    
    # Add to closed
    closed_data.append(opportunity)
    
    print(f"✅ Moved '{name}' to closed opportunities")
    return True


def interactive_mode():
    """Run in interactive mode"""
    active_data, closed_data = load_data()
    
    print("\n=== Move Opportunity to Closed ===\n")
    
    # Show categories
    print("Available categories:")
    if 'categories' in active_data:
        for i, cat in enumerate(active_data['categories'].keys(), 1):
            print(f"  {i}. {cat}")
    
    category = input("\nEnter category name: ").strip()
    
    # Show opportunities in category
    if category in active_data.get('categories', {}):
        print(f"\nOpportunities in '{category}':")
        for i, opp in enumerate(active_data['categories'][category], 1):
            print(f"  {i}. {opp['name']}")
    elif 'closingSoon' in active_data:
        print("\nOpportunities in 'Closing Soon':")
        for i, opp in enumerate(active_data['closingSoon'], 1):
            print(f"  {i}. {opp['name']}")
    
    name = input("\nEnter opportunity name: ").strip()
    closed_date = input("Enter closed date (YYYY-MM-DD, or press Enter for today): ").strip()
    
    if not closed_date:
        closed_date = datetime.now().strftime('%Y-%m-%d')
    
    if move_to_closed(active_data, closed_data, category, name, closed_date):
        save_data(active_data, closed_data)
        print("\n✅ Files updated successfully!")
        print("Don't forget to run: python generate_readme.py")
    else:
        print("\n❌ Operation cancelled")


def main():
    parser = argparse.ArgumentParser(
        description='Move opportunities from active to closed'
    )
    parser.add_argument('--category', help='Category name')
    parser.add_argument('--name', help='Opportunity name')
    parser.add_argument('--date', help='Closed date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.category and args.name:
        # Command-line mode
        active_data, closed_data = load_data()
        
        if move_to_closed(active_data, closed_data, args.category, args.name, args.date):
            save_data(active_data, closed_data)
            print("✅ Files updated successfully!")
            print("Don't forget to run: python generate_readme.py")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()