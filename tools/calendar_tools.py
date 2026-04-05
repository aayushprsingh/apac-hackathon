"""
Google Calendar API Tools for Cortex
Provides calendar reading and event creation via Google Calendar API
"""

import os
from datetime import datetime, timedelta
from typing import Optional

# Lazy-load the Calendar API service
_calendar_service = None


def get_calendar_service():
    """Get or create the Google Calendar API service (lazy initialization)."""
    global _calendar_service
    if _calendar_service is not None:
        return _calendar_service
    
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    
    token_file = "token.json"
    creds = None
    
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/calendar'])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError(
                "Calendar API not authenticated. To fix:\n"
                "1. Go to https://console.cloud.google.com/apis/credentials\n"
                "2. Create OAuth 2.0 Client ID (Desktop app)\n"
                "3. Download and save as credentials.json\n"
                "4. Run: python tools/authenticate.py --calendar\n"
            )
    
    _calendar_service = build('calendar', 'v3', credentials=creds)
    return _calendar_service


def list_events(day: str = None, max_results: int = 20) -> list:
    """
    List calendar events for a specific day or upcoming period.
    
    Args:
        day: Date in 'YYYY-MM-DD' format. If None, shows upcoming events.
        max_results: Maximum number of events to return (default 20)
    
    Returns:
        list of event dicts with id, summary, start, end, attendees, description
    """
    try:
        service = get_calendar_service()
        
        if day:
            # Specific day: start of day to end of day
            start_dt = f"{day}T00:00:00+05:30"
            end_dt = f"{day}T23:59:59+05:30"
            time_min = start_dt
            time_max = end_dt
        else:
            # Upcoming: now to 7 days from now
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=7)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        formatted = []
        for event in events:
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Parse start/end times
            start_str = start.get('dateTime', start.get('date', 'All day'))
            end_str = end.get('dateTime', end.get('date', ''))
            
            # Check if it's an all-day event
            is_all_day = 'date' in start and 'dateTime' not in start
            
            formatted.append({
                'id': event['id'],
                'summary': event.get('summary', '(No title)'),
                'start': start_str,
                'end': end_str,
                'is_all_day': is_all_day,
                'location': event.get('location', ''),
                'description': event.get('description', ''),
                'attendees': [
                    a.get('email', '') 
                    for a in event.get('attendees', []) 
                    if a.get('email')
                ],
                'organizer': event.get('organizer', {}).get('email', ''),
                'status': event.get('status', ''),
                'created': event.get('created', ''),
            })
        
        return formatted
    except RuntimeError as e:
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": f"Failed to list events: {str(e)}"}]


def get_todays_events(max_results: int = 20) -> list:
    """Convenience: get today's events."""
    today = datetime.now().strftime('%Y-%m-%d')
    return list_events(day=today, max_results=max_results)


def get_tomorrow_events(max_results: int = 20) -> list:
    """Convenience: get tomorrow's events."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    return list_events(day=tomorrow, max_results=max_results)


def get_event(event_id: str) -> dict:
    """
    Get a specific calendar event by ID.
    
    Args:
        event_id: The calendar event ID
    
    Returns:
        dict with full event details
    """
    try:
        service = get_calendar_service()
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        start = event.get('start', {})
        end = event.get('end', {})
        
        return {
            'id': event['id'],
            'summary': event.get('summary', '(No title)'),
            'start': start.get('dateTime', start.get('date', 'All day')),
            'end': end.get('dateTime', end.get('date', '')),
            'is_all_day': 'date' in start and 'dateTime' not in start,
            'location': event.get('location', ''),
            'description': event.get('description', ''),
            'attendees': [
                {
                    'email': a.get('email', ''),
                    'name': a.get('displayName', ''),
                    'status': a.get('responseStatus', ''),
                }
                for a in event.get('attendees', [])
            ],
            'organizer': {
                'email': event.get('organizer', {}).get('email', ''),
                'name': event.get('organizer', {}).get('displayName', ''),
            },
            'status': event.get('status', ''),
            'html_link': event.get('htmlLink', ''),
            'created': event.get('created', ''),
            'updated': event.get('updated', ''),
        }
    except Exception as e:
        return {"error": f"Failed to get event: {str(e)}"}


def create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: list = None,
    timezone: str = "Asia/Kolkata"
) -> dict:
    """
    Create a new calendar event.
    
    Args:
        title: Event title/summary
        start_time: Start time in ISO format (e.g., '2026-04-06T10:00:00+05:30')
        end_time: End time in ISO format (e.g., '2026-04-06T11:00:00+05:30')
        description: Optional event description
        location: Optional location
        attendees: Optional list of attendee emails
        timezone: Timezone (default: Asia/Kolkata for IST)
    
    Returns:
        dict with created event details
    """
    try:
        service = get_calendar_service()
        
        event = {
            'summary': title,
            'description': description,
            'location': location,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()
        
        return {
            'id': created_event['id'],
            'summary': created_event.get('summary', ''),
            'start': created_event.get('start', {}).get('dateTime', ''),
            'end': created_event.get('end', {}).get('dateTime', ''),
            'link': created_event.get('htmlLink', ''),
            'status': 'Event created',
        }
    except Exception as e:
        return {"error": f"Failed to create event: {str(e)}"}


def quick_add_event(text: str) -> dict:
    """
    Quick-add an event using Google's natural language parsing.
    
    Args:
        text: Natural language event description
               e.g., "Meeting with Rahul tomorrow at 3pm"
    
    Returns:
        dict with created event details
    """
    try:
        service = get_calendar_service()
        created_event = service.events().quickAdd(
            calendarId='primary',
            text=text
        ).execute()
        
        return {
            'id': created_event['id'],
            'summary': created_event.get('summary', ''),
            'start': created_event.get('start', {}).get('dateTime', created_event.get('start', {}).get('date', '')),
            'end': created_event.get('end', {}).get('dateTime', created_event.get('end', {}).get('date', '')),
            'link': created_event.get('htmlLink', ''),
            'status': 'Event created via quick add',
        }
    except Exception as e:
        return {"error": f"Failed to quick-add event: {str(e)}"}


def check_availability(start_date: str, end_date: str) -> dict:
    """
    Check free/busy information for a date range.
    
    Args:
        start_date: Start ISO datetime
        end_date: End ISO datetime
    
    Returns:
        dict with busy periods
    """
    try:
        service = get_calendar_service()
        
        body = {
            'timeMin': start_date,
            'timeMax': end_date,
            'items': [{'id': 'primary'}],
        }
        
        freebusy = service.freebusy().query(body=body).execute()
        
        periods = freebusy.get('calendars', {}).get('primary', {}).get('busy', [])
        
        return {
            'start': start_date,
            'end': end_date,
            'busy_periods': periods,
            'is_free': len(periods) == 0,
        }
    except Exception as e:
        return {"error": f"Failed to check availability: {str(e)}"}
