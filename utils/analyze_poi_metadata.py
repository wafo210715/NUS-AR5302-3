"""
Analyze POI metadata to support Part 4 analysis.
"""

import pandas as pd
import json
from collections import Counter

df = pd.read_csv('data/sg_pois_all.csv')

print('='*60)
print('POI Metadata for Part 4 Analysis')
print('='*60)

# 1. Core metadata for quality filtering
print('\n1. QUALITY METADATA (for filtering low-quality POIs/stations)')
print('-'*50)
v1_count = sum(df['version'] == 1)
print(f'   version: edit history (1-20), {v1_count} are v1 ({v1_count/len(df)*100:.1f}%)')
print(f'   timestamp: last edit time (2009-2026)')
print(f'   user_id: contributor info ({df["user_id"].nunique()} unique mappers)')
print(f'   changeset_id: edit batch ID')

# 2. opening_hours analysis
print('\n2. INTRA-DAY DYNAMICS (opening_hours tag)')
print('-'*50)

# Sample opening_hours values
opening_hours_samples = []
oh_poi_classes = []

sample_size = 10000
for idx, row in df.head(sample_size).iterrows():
    try:
        tags = json.loads(row['all_tags'].replace('""', '"'))
        if 'opening_hours' in tags:
            oh = tags['opening_hours']
            opening_hours_samples.append(oh)
            # Get primary POI class
            for key in ['amenity', 'shop', 'leisure', 'tourism', 'office', 'healthcare', 'craft', 'historic']:
                val = row[key]
                if pd.notna(val) and val != '':
                    oh_poi_classes.append(f'{key}={val}')
                    break
    except:
        pass

print(f'   Coverage: {len(opening_hours_samples)}/{sample_size} ({len(opening_hours_samples)/sample_size*100:.1f}%)')
print(f'   Unique values: {len(set(opening_hours_samples))}')

# Show common opening_hours patterns
common_oh = Counter(opening_hours_samples).most_common(15)
print(f'   Top 15 patterns:')
for val, count in common_oh:
    print(f'     \"{val}\": {count}')

# POI classes with opening_hours
if oh_poi_classes:
    print(f'\n   POI classes most likely to have opening_hours:')
    oh_class_counts = Counter(oh_poi_classes).most_common(10)
    for cls, count in oh_class_counts:
        print(f'     {cls}: {count}')

# 3. All available metadata
print('\n3. ALL AVAILABLE METADATA FIELDS')
print('-'*50)
print('   Location: lat, lon (WGS84)')
print('   POI type: osm_type (node/way)')
print('   POI keys: amenity, shop, leisure, tourism, office, healthcare, craft, historic')
print('   Labels: name ({}% have names)'.format(round(df['name'].notna().sum()/len(df)*100, 1)))
print('   Raw data: all_tags (complete tag dump)')

# 4. Part 4 requirements
print('\n4. PART 4 REQUIREMENTS VS AVAILABLE DATA')
print('-'*50)
print('   ✅ LDA station classification: station_topic_classification.csv')
print('      - Dominant topic per station')
print('      - Topic probability distributions (gamma)')
print('      - Station coordinates')
print()
print('   ✅ NUS vs NTU comparison: Can be derived')
print('      - Use station_mapping.csv to identify NUS/NTU stations')
print('      - Join with LDA classification')
print('      - Compare topic distributions')
print()
print('   ⚠️  Intra-day dynamics (opening_hours): Limited coverage (~8%)')
print('      - Only ~8% of POIs have opening_hours tag')
print('      - May need to limit scope to well-covered POI classes')
print()
print('   ✅ Quality filtering: VERSION, TIMESTAMP, USER_ID available')
print('      - Can filter low-quality stations')
print('      - Can analyze data quality impact on results')

print('\n' + '='*60)
