from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import io
from datetime import datetime

class SpeechAnalysisPDF:
    """Generate PDF reports for speech analysis results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=20
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY
        ))
    
    def generate_pdf(self, analysis, user):
        """Generate a PDF report for the analysis"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        story = []
        
        # Title
        title = Paragraph("Speech Analysis Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))
        
        # User info section
        user_info = f"""
        <b>User:</b> {user.name or 'N/A'}<br/>
        <b>Email:</b> {user.email or 'N/A'}<br/>
        <b>Analysis Date:</b> {analysis.created_at.strftime('%B %d, %Y at %I:%M %p') if analysis.created_at else 'N/A'}<br/>
        <b>File:</b> {analysis.filename or 'N/A'}<br/>
        <b>Duration:</b> {self._format_duration(analysis.duration) if analysis.duration else 'N/A'}
        """
        story.append(Paragraph(user_info, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Key Metrics Table
        story.append(Paragraph("Key Metrics", self.styles['SectionHeading']))
        metrics_data = [
            ['Metric', 'Value'],
            ['Dominant Emotion', analysis.dominant_emotion or 'N/A'],
            ['Average Words Per Second', f"{analysis.avg_wps:.2f}" if analysis.avg_wps else 'N/A'],
            ['Clarity Score', f"{analysis.clarity_score:.1f}%" if analysis.clarity_score else 'N/A'],
            ['Total Words', str(analysis.total_words) if analysis.total_words else 'N/A']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Emotion Analysis Section
        if analysis.emotion_segments:
            story.append(Paragraph("Emotion Timeline", self.styles['SectionHeading']))
            
            # Emotion metrics if available
            if analysis.emotion_metrics:
                emotion_metrics = analysis.emotion_metrics
                emotion_text = f"""
                <b>Main Emotion:</b> {emotion_metrics.get('main_emotion', 'N/A')} 
                ({emotion_metrics.get('main_emotion_percentage', 0):.1f}%)<br/>
                <b>Emotion Diversity:</b> {emotion_metrics.get('emotion_diversity', 0)} different emotions<br/>
                <b>Versatility Score:</b> {emotion_metrics.get('versatility_score', 0):.1f}%
                """
                story.append(Paragraph(emotion_text, self.styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
            
            # Emotion segments table
            emotion_data = [['Time Range', 'Emotion']]
            for segment in analysis.emotion_segments[:20]:  # Limit to first 20 segments
                if isinstance(segment, dict):
                    emotion_data.append([
                        segment.get('time_range', 'N/A'),
                        segment.get('emotion', 'N/A')
                    ])
                elif isinstance(segment, (list, tuple)) and len(segment) >= 2:
                    emotion_data.append([segment[0], segment[1]])
            
            if len(emotion_data) > 1:
                emotion_table = Table(emotion_data, colWidths=[2.5*inch, 2.5*inch])
                emotion_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                story.append(emotion_table)
                
                if len(analysis.emotion_segments) > 20:
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(
                        f"<i>Showing first 20 of {len(analysis.emotion_segments)} segments</i>",
                        self.styles['Normal']
                    ))
            
            story.append(Spacer(1, 0.3*inch))
        
        # Transcription Section
        if analysis.transcription_data:
            story.append(Paragraph("Transcription", self.styles['SectionHeading']))
            
            # Speech clarity metrics if available
            if analysis.speech_clarity:
                clarity = analysis.speech_clarity
                clarity_text = f"""
                <b>Average Words Per Segment:</b> {clarity.get('avg_words_per_segment', 0):.1f}<br/>
                <b>WPS Variation:</b> {clarity.get('wps_variation', 0):.2f}<br/>
                """
                if clarity.get('issues'):
                    issues_text = "<b>Issues Detected:</b><br/>" + "<br/>".join(
                        f"• {issue}" for issue in clarity['issues'][:5]
                    )
                    clarity_text += issues_text
                
                story.append(Paragraph(clarity_text, self.styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
            
            # Transcription segments
            transcription_text = ""
            for i, segment in enumerate(analysis.transcription_data[:15], 1):  # Limit to first 15 segments
                if isinstance(segment, dict):
                    start = self._format_timestamp(segment.get('start', 0))
                    end = self._format_timestamp(segment.get('end', 0))
                    text = segment.get('text', '')
                    emotion = segment.get('emotion', 'N/A')
                    wps = segment.get('wps', 0)
                    
                    transcription_text += f"""
                    <b>Segment {i} ({start} - {end}):</b> {text}<br/>
                    <i>Emotion: {emotion} | WPS: {wps:.2f}</i><br/><br/>
                    """
            
            if transcription_text:
                story.append(Paragraph(transcription_text, self.styles['BodyText']))
                
                if len(analysis.transcription_data) > 15:
                    story.append(Paragraph(
                        f"<i>Showing first 15 of {len(analysis.transcription_data)} transcription segments</i>",
                        self.styles['Normal']
                    ))
            
            story.append(Spacer(1, 0.3*inch))
        
        # Gemini AI Analysis Section
        if analysis.gemini_analysis:
            story.append(Paragraph("AI Analysis & Insights", self.styles['SectionHeading']))
            
            gemini = analysis.gemini_analysis
            
            # Summary
            if gemini.get('summary'):
                story.append(Paragraph("<b>Summary:</b>", self.styles['Normal']))
                story.append(Paragraph(gemini['summary'], self.styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
            
            # Strengths
            if gemini.get('strengths'):
                strengths_text = "<b>Strengths:</b><br/>"
                if isinstance(gemini['strengths'], list):
                    strengths_text += "<br/>".join(f"• {strength}" for strength in gemini['strengths'])
                else:
                    strengths_text += str(gemini['strengths'])
                story.append(Paragraph(strengths_text, self.styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
            
            # Improvement Areas
            if gemini.get('improvement_areas'):
                improvements_text = "<b>Areas for Improvement:</b><br/>"
                if isinstance(gemini['improvement_areas'], list):
                    improvements_text += "<br/>".join(f"• {area}" for area in gemini['improvement_areas'])
                else:
                    improvements_text += str(gemini['improvement_areas'])
                story.append(Paragraph(improvements_text, self.styles['BodyText']))
                story.append(Spacer(1, 0.2*inch))
            
            # Coaching Tips
            if gemini.get('coaching_tips'):
                tips_text = "<b>Coaching Tips:</b><br/>"
                tips_list = gemini['coaching_tips']
                if isinstance(tips_list, list):
                    for i, tip in enumerate(tips_list, 1):
                        tip_text = tip if isinstance(tip, str) else (tip.get('tip', '') if isinstance(tip, dict) else str(tip))
                        tips_text += f"<b>{i}.</b> {tip_text}<br/>"
                else:
                    tips_text += str(tips_list)
                story.append(Paragraph(tips_text, self.styles['BodyText']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"<i>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _format_duration(self, seconds):
        """Format duration in seconds to MM:SS format"""
        if not seconds:
            return 'N/A'
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _format_timestamp(self, seconds):
        """Format timestamp in seconds to MM:SS format"""
        if not seconds:
            return '00:00'
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
