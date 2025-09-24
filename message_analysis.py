#!/usr/bin/env python3
"""
Messages Wrapped - Analysis Script (Updated for CSV format)
Analyzes iMessage conversation data and generates statistics
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from collections import Counter
import re
import numpy as np

class MessageAnalyzer:
    def __init__(self, csv_path):
        """Initialize analyzer with CSV file path"""
        print("Loading CSV data...")
        self.df = pd.read_csv(csv_path)
        print(f"Raw data shape: {self.df.shape}")
        print(f"Columns: {list(self.df.columns)}")
        print(f"Date column sample:\n{self.df['Date'].head()}")
        
        # Rename columns to match expected format
        self.df = self.df.rename(columns={
            'Date': 'date',
            'Sender': 'sender', 
            'Message': 'text'
        })
        
        # Map sender names
        sender_mapping = {
            'Catherine': 'Her',
            'Ryan': 'You'
        }
        self.df['sender'] = self.df['sender'].map(sender_mapping)
        
        # Convert dates and add debug info
        print("\nConverting dates...")
        self.df['date'] = pd.to_datetime(self.df['date'])
        print(f"After date conversion:\n{self.df['date'].head()}")
        print(f"Date range: {self.df['date'].min()} to {self.df['date'].max()}")
        
        # Check for any invalid dates
        invalid_dates = self.df['date'].isna().sum()
        if invalid_dates > 0:
            print(f"WARNING: {invalid_dates} invalid dates found and will be excluded")
            self.df = self.df.dropna(subset=['date'])
        
        self.df = self.df.sort_values('date')
        
        # Clean up text column - remove NaN
        self.df['text'] = self.df['text'].fillna('')
        
        # Add helpful columns
        self.df['year'] = self.df['date'].dt.year
        self.df['month'] = self.df['date'].dt.month
        self.df['day_of_week'] = self.df['date'].dt.day_name()
        self.df['hour'] = self.df['date'].dt.hour
        self.df['word_count'] = self.df['text'].str.split().str.len().fillna(0)
        
        # Debug: Check year distribution
        print("\nYear distribution:")
        year_counts = self.df['year'].value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"  {year}: {count:,} messages")
        
        # Debug: Check sender distribution
        print("\nSender distribution:")
        sender_counts = self.df['sender'].value_counts()
        for sender, count in sender_counts.items():
            print(f"  {sender}: {count:,} messages")
        
        print(f"\nTotal messages loaded: {len(self.df):,}")
        print(f"Date range: {self.df['date'].min().date()} to {self.df['date'].max().date()}")
    
    def basic_stats(self):
        """Generate basic conversation statistics"""
        print("Calculating basic stats...")
        
        total_days = (self.df['date'].max() - self.df['date'].min()).days
        
        you_count = len(self.df[self.df['sender'] == 'You'])
        her_count = len(self.df[self.df['sender'] == 'Her'])
        total_count = len(self.df)
        
        stats = {
            'total_messages': total_count,
            'date_range': {
                'first_message': str(self.df['date'].min()),
                'last_message': str(self.df['date'].max()),
                'days_talking': total_days
            },
            'by_sender': {
                'you': {
                    'count': you_count,
                    'percentage': round(you_count / total_count * 100, 1) if total_count > 0 else 0
                },
                'her': {
                    'count': her_count,
                    'percentage': round(her_count / total_count * 100, 1) if total_count > 0 else 0
                }
            },
            'averages': {
                'messages_per_day': round(total_count / (total_days + 1), 1) if total_days >= 0 else 0,
                'words_per_message': {
                    'overall': round(self.df['word_count'].mean(), 1),
                    'you': round(self.df[self.df['sender'] == 'You']['word_count'].mean(), 1) if you_count > 0 else 0,
                    'her': round(self.df[self.df['sender'] == 'Her']['word_count'].mean(), 1) if her_count > 0 else 0
                }
            }
        }
        return stats
    
    def time_patterns(self):
        """Analyze messaging patterns by time"""
        print("Analyzing time patterns...")
        
        # Create month-year strings for grouping (this fixes the JSON serialization issue)
        self.df['month_year'] = self.df['date'].dt.strftime('%Y-%m')
        
        patterns = {
            'by_hour': self.df.groupby(['hour', 'sender']).size().unstack(fill_value=0).to_dict(),
            'by_day': self.df.groupby(['day_of_week', 'sender']).size().unstack(fill_value=0).to_dict(),
            'by_month': self.df.groupby(['month_year', 'sender']).size().unstack(fill_value=0).to_dict(),
            'by_year': self.df.groupby(['year', 'sender']).size().unstack(fill_value=0).to_dict(),
            'peak_hour': {
                'overall': int(self.df['hour'].mode()[0]) if len(self.df) > 0 else 0,
                'you': int(self.df[self.df['sender'] == 'You']['hour'].mode()[0]) if len(self.df[self.df['sender'] == 'You']) > 0 else 0,
                'her': int(self.df[self.df['sender'] == 'Her']['hour'].mode()[0]) if len(self.df[self.df['sender'] == 'Her']) > 0 else 0
            },
            'peak_day': {
                'overall': self.df['day_of_week'].mode()[0] if len(self.df) > 0 else 'N/A',
                'you': self.df[self.df['sender'] == 'You']['day_of_week'].mode()[0] if len(self.df[self.df['sender'] == 'You']) > 0 else 'N/A',
                'her': self.df[self.df['sender'] == 'Her']['day_of_week'].mode()[0] if len(self.df[self.df['sender'] == 'Her']) > 0 else 'N/A'
            }
        }
        
        return patterns
    
    def emoji_analysis(self):
        """Analyze emoji usage"""
        print("Analyzing emojis...")
        
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002700-\U000027BF"  # Dingbats
            "\U00002600-\U000026FF"  # Miscellaneous Symbols
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "]+", 
            flags=re.UNICODE
        )
        
        def extract_emojis(text):
            if pd.isna(text) or text == '':
                return []
            return emoji_pattern.findall(str(text))
        
        # Extract all emojis
        self.df['emojis'] = self.df['text'].apply(extract_emojis)
        
        # Count emojis by sender
        you_emojis = [e for emojis in self.df[self.df['sender'] == 'You']['emojis'] for e in emojis]
        her_emojis = [e for emojis in self.df[self.df['sender'] == 'Her']['emojis'] for e in emojis]
        
        return {
            'total_emojis': {
                'you': len(you_emojis),
                'her': len(her_emojis)
            },
            'top_emojis': {
                'you': dict(Counter(you_emojis).most_common(10)),
                'her': dict(Counter(her_emojis).most_common(10))
            },
            'emoji_diversity': {
                'you': len(set(you_emojis)),
                'her': len(set(her_emojis))
            }
        }
    
    def word_analysis(self):
        """Analyze most common words and phrases"""
        print("Analyzing words and phrases...")
        
        # Common words to exclude
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
                     'i', 'you', 'he', 'she', 'it', 'we', 'they', 'that', 'this', 'my',
                     'your', 'im', 'dont', 'just', 'so', 'like', 'get', 'got', 'its', 'not'}
        
        def get_top_words(text_series, n=20):
            words = []
            for text in text_series.dropna():
                if text and str(text).strip():
                    words.extend([w.lower().strip('.,!?";:()[]{}') for w in str(text).split() 
                                if len(w) > 2 and w.lower() not in stop_words and w.isalpha()])
            return dict(Counter(words).most_common(n))
        
        # Get top words for each person
        you_text = self.df[self.df['sender'] == 'You']['text']
        her_text = self.df[self.df['sender'] == 'Her']['text']
        
        return {
            'top_words': {
                'you': get_top_words(you_text),
                'her': get_top_words(her_text)
            },
            'unique_phrases': self.find_unique_phrases()
        }
    
    def find_unique_phrases(self):
        """Find frequently used 2-3 word phrases (potential inside jokes)"""
        def get_ngrams(text_series, n=2):
            phrases = []
            for text in text_series.dropna():
                if text and str(text).strip():
                    words = str(text).lower().split()
                    for i in range(len(words) - n + 1):
                        phrase = ' '.join(words[i:i+n])
                        if all(len(w) > 2 for w in words[i:i+n]):
                            phrases.append(phrase)
            return phrases
        
        # Get 2-word and 3-word phrases
        bigrams = get_ngrams(self.df['text'], 2)
        trigrams = get_ngrams(self.df['text'], 3)
        
        # Filter for interesting phrases (appearing at least 5 times for this smaller dataset)
        bigram_counts = Counter(bigrams)
        trigram_counts = Counter(trigrams)
        
        interesting_bigrams = {k: v for k, v in bigram_counts.items() if v >= 3}
        interesting_trigrams = {k: v for k, v in trigram_counts.items() if v >= 2}
        
        return {
            'two_word': dict(sorted(interesting_bigrams.items(), key=lambda x: x[1], reverse=True)[:10]),
            'three_word': dict(sorted(interesting_trigrams.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def conversation_dynamics(self):
        """Analyze conversation dynamics"""
        print("Analyzing conversation dynamics...")
        
        # Calculate response times
        self.df['prev_sender'] = self.df['sender'].shift(1)
        self.df['time_diff'] = self.df['date'].diff()
        
        # Only consider responses (when sender changes)
        responses = self.df[self.df['sender'] != self.df['prev_sender']].copy()
        responses = responses[responses['time_diff'] < timedelta(hours=12)]  # Exclude very long gaps
        
        # Average response time
        you_responses = responses[responses['sender'] == 'You']['time_diff']
        her_responses = responses[responses['sender'] == 'Her']['time_diff']
        
        # Find conversation streaks
        self.df['date_only'] = self.df['date'].dt.date
        daily_messages = self.df.groupby('date_only').size()
        
        # Find longest streak of consecutive days
        dates = sorted(daily_messages.index)
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return {
            'response_times': {
                'you': {
                    'average_minutes': round(you_responses.mean().total_seconds() / 60, 1) if len(you_responses) > 0 else 0,
                    'median_minutes': round(you_responses.median().total_seconds() / 60, 1) if len(you_responses) > 0 else 0
                },
                'her': {
                    'average_minutes': round(her_responses.mean().total_seconds() / 60, 1) if len(her_responses) > 0 else 0,
                    'median_minutes': round(her_responses.median().total_seconds() / 60, 1) if len(her_responses) > 0 else 0
                }
            },
            'longest_streak_days': max_streak,
            'night_owl_vs_early_bird': {
                'late_night_messages': len(self.df[self.df['hour'].isin([0, 1, 2, 3, 4, 5])]),
                'early_morning_messages': len(self.df[self.df['hour'].isin([6, 7, 8, 9])])
            }
        }
    
    def special_phrases(self):
        """Look for special phrases like 'I love you', 'miss you', etc."""
        print("Analyzing special phrases...")
        
        phrases = {
            'love': r'(?:love you|love ya|luv you|luv u|love u|ily|ilysm|ilysfm|ilyvm|ilym|ilu|ilusm|ly|lysm|lysfm|love youu+|luv ya|love you so much|love you too|love you more|love you most|143)',
            'miss': r'\b(?:miss you|miss u|missin you|missing you|miss ya|missed you|miss you so much|missss you|miss youu+|i miss you|i miss u|imy|imysm|imysfm|miss your)\b',
            'sorry': r'\b(?:sorry|sry|srry|apologize|apologies|my bad|my fault|forgive me|i\'m sorry|im sorry)\b',
            'thanks': r'\b(?:thank you|thanks|thank u|thankyou|thx|thnx|ty|tyy+|tysm|tysfm|appreciate|grateful)\b',
            'good_morning': r'\b(?:good morning|goodmorning|gm|g\'morning|gmorning|morning babe|morning baby|morning love|mornin|buenos dias)\b',
            'good_night': r'\b(?:good night|goodnight|gn|gnnn+|nighty night|night night|sweet dreams|sleep well|sleep tight|night babe|night baby|night love|buenos noches)\b',
            'cute_names': r'\b(?:babe|baby|honey|hun|bby|bb|sweetheart|sweetie|love|my love|darling|dear|cutie|beautiful|handsome|gorgeous|pretty)\b',
            'excited': r'\b(?:can\'t wait|cant wait|excited|so excited|yay|yayyy+|woo|wooo+|woohoo|omg|omgg+|ahh|ahhh+|eee+)\b',
            'laughing': r'\b(?:lol|loll+|lmao|lmaoo+|lmfao|haha|hahaha+|hehe|hehehe+|dying|dead|😭😭)\b'
        }
        
        results = {}
        for phrase_type, pattern in phrases.items():
            # Get matches for each sender
            you_messages = self.df[self.df['sender'] == 'You']['text']
            her_messages = self.df[self.df['sender'] == 'Her']['text']
            
            you_count = you_messages.str.contains(pattern, case=False, na=False, regex=True).sum()
            her_count = her_messages.str.contains(pattern, case=False, na=False, regex=True).sum()
            
            results[phrase_type] = {
                'you': int(you_count),
                'her': int(her_count),
                'total': int(you_count + her_count)
            }
        
        return results
    
    def generate_full_analysis(self):
        """Generate complete analysis"""
        print("\n" + "="*60)
        print("STARTING FULL ANALYSIS")
        print("="*60)
        
        analysis = {}
        
        try:
            analysis['basic_stats'] = self.basic_stats()
            print("✅ Basic stats completed")
            
            analysis['time_patterns'] = self.time_patterns()
            print("✅ Time patterns completed")
            
            analysis['emoji_analysis'] = self.emoji_analysis()
            print("✅ Emoji analysis completed")
            
            analysis['word_analysis'] = self.word_analysis()
            print("✅ Word analysis completed")
            
            analysis['conversation_dynamics'] = self.conversation_dynamics()
            print("✅ Conversation dynamics completed")
            
            analysis['special_phrases'] = self.special_phrases()
            print("✅ Special phrases completed")
            
        except Exception as e:
            print(f"ERROR during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        
        # Add some fun calculated stats
        basic = analysis['basic_stats']
        emoji = analysis['emoji_analysis']
        dynamics = analysis['conversation_dynamics']
        phrases = analysis['special_phrases']
        
        analysis['fun_facts'] = {
            'messages_per_month': round(basic['total_messages'] / 
                                       (basic['date_range']['days_talking'] / 30), 1) if basic['date_range']['days_talking'] > 0 else 0,
            'who_talks_more': 'You' if basic['by_sender']['you']['count'] > basic['by_sender']['her']['count'] else 'Her',
            'who_uses_more_emojis': 'You' if emoji['total_emojis']['you'] > emoji['total_emojis']['her'] else 'Her',
            'who_writes_longer': 'You' if basic['averages']['words_per_message']['you'] > basic['averages']['words_per_message']['her'] else 'Her',
            'who_responds_faster': 'You' if dynamics['response_times']['you']['average_minutes'] < dynamics['response_times']['her']['average_minutes'] else 'Her' if dynamics['response_times']['her']['average_minutes'] > 0 else 'You',
            'who_says_love_more': 'You' if phrases['love']['you'] > phrases['love']['her'] else 'Her' if phrases['love']['her'] > 0 else 'Tied',
            'who_laughs_more': 'You' if phrases['laughing']['you'] > phrases['laughing']['her'] else 'Her' if phrases['laughing']['her'] > 0 else 'Tied'
        }
        
        print("✅ Fun facts calculated")
        return analysis

def main():
    # Path to your CSV file (from the message parser)
    csv_path = 'parsed_messages.csv'
    
    print("Messages Wrapped Analysis - Updated for CSV Format")
    print("=" * 60)
    
    try:
        # Initialize analyzer
        print("Initializing analyzer...")
        analyzer = MessageAnalyzer(csv_path)
        
        # Generate analysis
        print("\nGenerating comprehensive analysis...")
        results = analyzer.generate_full_analysis()
        
        if results is None:
            print("Analysis failed!")
            return
        
        # Save to JSON file
        output_path = 'messages_analysis_results.json'
        print(f"\nSaving results to {output_path}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"✅ Analysis complete! Results saved to {output_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total messages: {results['basic_stats']['total_messages']:,}")
        print(f"Date range: {results['basic_stats']['date_range']['days_talking']} days")
        print(f"  From: {results['basic_stats']['date_range']['first_message'][:10]}")
        print(f"  To: {results['basic_stats']['date_range']['last_message'][:10]}")
        print(f"Messages per day: {results['basic_stats']['averages']['messages_per_day']}")
        print(f"Who talks more: {results['fun_facts']['who_talks_more']}")
        print(f"Who uses more emojis: {results['fun_facts']['who_uses_more_emojis']}")
        print(f"Longest conversation streak: {results['conversation_dynamics']['longest_streak_days']} days")
        
        # Show breakdown by sender
        print(f"\nMessage breakdown:")
        print(f"  You (Ryan): {results['basic_stats']['by_sender']['you']['count']:,} ({results['basic_stats']['by_sender']['you']['percentage']}%)")
        print(f"  Her (Catherine): {results['basic_stats']['by_sender']['her']['count']:,} ({results['basic_stats']['by_sender']['her']['percentage']}%)")
        
        # Show special phrase counts
        print(f"\nSpecial phrases:")
        print(f"  'Love' expressions - You: {results['special_phrases']['love']['you']}, Her: {results['special_phrases']['love']['her']}")
        print(f"  'Miss' expressions - You: {results['special_phrases']['miss']['you']}, Her: {results['special_phrases']['miss']['her']}")
        print(f"  Cute names - You: {results['special_phrases']['cute_names']['you']}, Her: {results['special_phrases']['cute_names']['her']}")
        print(f"  Laughing/LOL - You: {results['special_phrases']['laughing']['you']}, Her: {results['special_phrases']['laughing']['her']}")
        
        print(f"\n✅ Analysis successfully completed!")
        
    except FileNotFoundError:
        print(f"ERROR: Could not find {csv_path}")
        print("Make sure you've run the message parser first to create the CSV file!")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()