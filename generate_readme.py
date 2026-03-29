#!/usr/bin/env python3
import json
from typing import TypedDict
from datetime import datetime, timedelta
import re

class Opportunity(TypedDict, total=False):
    name:        str
    url:         str
    field:       str
    location:    str
    ageCategory: str
    deadline:    str


class Certificate(TypedDict):
    name:  str
    url:   str
    field: str


class EducationResource(TypedDict):
    name:        str
    url:         str
    description: str


class PeopleCommunity(TypedDict):
    name:        str
    url:         str
    description: str


class OpportunitiesSchema(TypedDict):
    closingSoon:        list[Opportunity]
    categories:         dict[str, list[Opportunity]]
    certificates:       list[Certificate]
    educationResources: list[EducationResource]
    peopleCommunities:  list[PeopleCommunity]


class ClosedOpportunity(TypedDict, total=False):
    name:        str
    url:         str
    field:       str
    location:    str
    ageCategory: str
    deadline:    str
    closedDate:  str
    category:    str


def main():
    # Load active opportunities
    with open('data.json', 'r', encoding='utf-8') as f:
        data: OpportunitiesSchema = json.load(f)

    # Load closed opportunities
    try:
        with open('closed_opportunities.json', 'r', encoding='utf-8') as f:
            closed_data = json.load(f)
    except FileNotFoundError:
        closed_data = []

    # Auto-close expired opportunities
    print("Checking for expired opportunities...")
    moved = auto_close_expired_opportunities(data, closed_data)
    if moved > 0:
        print(f"Auto-closed {moved} expired opportunity/opportunities")
        # Save updated data
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        with open('closed_opportunities.json', 'w', encoding='utf-8') as f:
            json.dump(closed_data, f, indent=2, ensure_ascii=False)
    else:
        print("No expired opportunities found")

    # Generate content
    tables_content = generate_tables_section(data)
    
    # Generate index.md (for GitHub Pages - with front matter)
    with open('index_template.md', 'r', encoding='utf-8') as f:
        index_template = f.read()
    final_index = insert_generated_content(index_template, tables_content)
    with open('index.md', 'w', encoding='utf-8') as f:
        f.write(final_index)
    
    # Generate README.md (for GitHub repo - without front matter)
    with open('README_template.md', 'r', encoding='utf-8') as f:
        readme_template = f.read()
    final_readme = insert_generated_content(readme_template, tables_content)
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(final_readme)

    generate_closed_opportunities_page(closed_data)
    print("index.md, README.md, and CLOSED.md generated successfully!")


def insert_generated_content(template, tables_content):
    """Insert content while preserving front matter"""
    start_marker = "<!-- AUTO-GENERATED-TABLES-START -->"
    end_marker = "<!-- AUTO-GENERATED-TABLES-END -->"

    if start_marker not in template or end_marker not in template:
        # Fallback - append content
        return template + "\n\n" + tables_content
    
    start_index = template.index(start_marker) + len(start_marker)
    end_index = template.index(end_marker)

    return (
        template[:start_index]
        + "\n\n"
        + tables_content.strip()
        + "\n\n"
        + template[end_index:]
    )

def parse_deadline(deadline_str):
    """Parse deadline string and return date object"""
    if not deadline_str or deadline_str.lower() in ['na', 'rolling', 'n/a', '']:
        return None
    
    try:
        # Handle formats like "6 March", "March 6", "17 March"
        current_year = datetime.now().year
        
        # Try different date formats
        for fmt in ['%d %B', '%B %d', '%d %b', '%b %d']:
            try:
                parsed = datetime.strptime(deadline_str.strip(), fmt)
                # Add current year
                deadline = parsed.replace(year=current_year)
                
                # If deadline is in the past and we're in Q1 next year, 
                # it might have been from last year
                if deadline < datetime.now() - timedelta(days=365):
                    deadline = deadline.replace(year=current_year + 1)
                
                return deadline
            except ValueError:
                continue
        
        # Try full date format YYYY-MM-DD
        return datetime.strptime(deadline_str, '%Y-%m-%d')
    except:
        return None
    

def auto_close_expired_opportunities(data, closed_data):
    """Automatically move opportunities past their deadline to closed"""
    today = datetime.now()
    moved_count = 0
    
    # Check closingSoon
    if 'closingSoon' in data:
        to_remove = []
        for i, opp in enumerate(data['closingSoon']):
            deadline = parse_deadline(opp.get('deadline', ''))
            if deadline and deadline < today - timedelta(days=1):
                # Add to closed
                opp['category'] = 'Closing Soon'
                opp['closedDate'] = deadline.strftime('%Y-%m-%d')
                closed_data.append(opp)
                to_remove.append(i)
                moved_count += 1
                print(f"  ✓ Auto-closed: {opp['name']} (deadline: {opp.get('deadline')})")
        
        # Remove in reverse order to maintain indices
        for i in reversed(to_remove):
            data['closingSoon'].pop(i)
    
    # Check each category
    if 'categories' in data:
        for category, opportunities in data['categories'].items():
            to_remove = []
            for i, opp in enumerate(opportunities):
                deadline = parse_deadline(opp.get('deadline', ''))
                if deadline and deadline < today - timedelta(days=1):
                    # Add to closed
                    opp['category'] = category
                    opp['closedDate'] = deadline.strftime('%Y-%m-%d')
                    closed_data.append(opp)
                    to_remove.append(i)
                    moved_count += 1
                    print(f"  ✓ Auto-closed: {opp['name']} from {category} (deadline: {opp.get('deadline')})")
            
            # Remove in reverse order
            for i in reversed(to_remove):
                opportunities.pop(i)
    
    return moved_count

def generate_tables_section(data):
    content = ""

    # Closing Soon
    closing_soon = data.get('closingSoon', [])
    if closing_soon:
        content += "## ❗ Closing Soon\n\n"
        content += generate_table(
            ['Name', 'Field', 'Deadline'],
            closing_soon,
            ['name', 'field', 'deadline']
        )
        content += "\n---\n\n"

    # Categories
    for category, opportunities in data.get('categories', {}).items():
        if not opportunities:
            continue

        content += f"## {category}\n\n"

        if category == "Certificates":
            content += generate_table(
                ['Name', 'Field'],
                opportunities,
                ['name', 'field']
            )
        else:
            content += generate_table(
                ['Name', 'Field', 'Location', 'Age Category', 'Deadline'],
                opportunities,
                ['name', 'field', 'location', 'ageCategory', 'deadline']
            )

        content += "\n---\n\n"

    # Education Resources
    resources = data.get('educationResources', [])
    if resources:
        content += "## Education Resources\n\n"
        for resource in resources:
            content += f"- [{resource['name']}]({resource['url']}): {resource['description']}  \n"
        content += "\n---\n\n"

    # People/Communities
    people = data.get('peopleCommunities', [])
    if people:
        content += "## People/Communities/Job Boards\n\n"
        for item in people:
            description = item.get('description', '')
            content += f"- [{item['name']}]({item['url']}): {description}  \n"
        content += "\n---\n\n"

    return content


def generate_table(headers: list[str], items: list[Opportunity], fields: list[str]) -> str:
    """Generate a markdown table with given headers and items"""
    if not items:
        return ""

    # Table header
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["-------"] * len(headers)) + " |\n"

    # Table rows
    for item in items:
        row = []
        for field_index, field in enumerate(fields):
            value = str(item.get(field, "")).replace("|", "\\|")

            # Create hyperlink for name field
            if field_index == 0:
                url = item.get('url', '')
                if url and url != 'NA':
                    value = f"[{value}]({url})"

            row.append(value)
        table += "| " + " | ".join(row) + " |  \n"

    return table


def generate_closed_opportunities_page(closed_opportunities):
    """Generate CLOSED.md using template"""
    
    # Try to load template with front matter
    try:
        with open('CLOSED_template.md', 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        # Fallback template if file doesn't exist
        template = """---
layout: default
title: Closed Opportunities Archive
---
# 🗄️ Closed Opportunities Archive

This page contains opportunities that have closed or expired. We keep them here for reference and to help you discover similar opportunities that may reopen in the future.

> [!TIP]
> Many of these opportunities run annually! Bookmark this page and check back next year.

**[← Back to Active Opportunities](README.md)**

---

<!-- AUTO-GENERATED-CONTENT-START -->
<!-- AUTO-GENERATED-CONTENT-END -->

### Notes

- These opportunities have passed their deadline or are no longer accepting applications
- Check if similar opportunities will be offered in the future
- Many programs run annually - set a reminder to apply next year!

**[← Back to Active Opportunities](README.md)**
"""
    
    content = ""
    
    if not closed_opportunities:
        content = "_No closed opportunities yet._\n"
    else:
        # Group by category
        by_category = {}
        for opp in closed_opportunities:
            category = opp.get('category', 'Other')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(opp)
        
        # Sort by closed date (most recent first)
        for category in by_category:
            by_category[category].sort(
                key=lambda x: x.get('closedDate', ''), 
                reverse=True
            )
        
        # Generate tables by category
        for category in sorted(by_category.keys()):
            opportunities = by_category[category]
            content += f"## {category}\n\n"
            
            headers = ['Name', 'Field', 'Location', 'Deadline', 'Closed']
            fields = ['name', 'field', 'location', 'deadline', 'closedDate']
            
            content += generate_table(headers, opportunities, fields)
            content += "\n---\n\n"
    
    final_closed = insert_generated_content(template, content)
    
    with open('CLOSED.md', 'w', encoding='utf-8') as f:
        f.write(final_closed)


if __name__ == "__main__":
    main()
