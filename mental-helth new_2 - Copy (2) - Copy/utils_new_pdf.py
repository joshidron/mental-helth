    import os
    from docx import Document
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from datetime import datetime
    import re

    # Font paths
    FONT_DIR = "static/fonts"
    FONT_PATH_NIRMALA = os.path.join(FONT_DIR, "Nirmala.ttc")

    # PDF Translations (same as before)
    PDF_TRANSLATIONS = {
        'en': {
            'title': 'PRAJNA PATH',
            'subtitle': 'Your Personalized Wellness Journey',
            'name': 'Name',
            'age': 'Age',
            'profession': 'Profession',
            'date': 'Date',
            'disclaimer': 'Disclaimer: This report is for informational purposes only and does not replace professional medical advice.',
            'page': 'Page',
            'no_data': 'No specific advice found for this section. Please consult a specialist.',
            'main symptoms': 'Main Symptoms',
            'myths': 'Myths',
            'routine': 'Daily Routine',
            'social': 'Social Activities',
            'food': 'Food Habits',
            'exercise': 'Exercise',
            'general': 'General'
        },
        'hi': {
            'title': 'PRAJNA PATH',
            'subtitle': 'आपकी व्यक्तिगत मानसिक स्वास्थ्य यात्रा',
            'name': 'नाम',
            'age': 'उम्र',
            'profession': 'पेशा',
            'date': 'तारीख',
            'disclaimer': 'Disclaimer: This report is for informational purposes only and does not replace professional medical advice.',
            'page': 'पृष्ठ',
            'no_data': 'इस खंड के लिए कोई विशिष्ट सलाह नहीं मिली। कृपया किसी विशेषज्ञ से सलाह लें।',
            'main symptoms': 'मुख्य लक्षण',
            'myths': 'भ्रामक धारणाएं (मिथक)',
            'routine': 'दैनिक दिनचर्या',
            'social': 'सामाजिक गतिविधियाँ',
            'food': 'भोजन की आदतें',
            'exercise': 'व्यायाम',
            'general': 'सामान्य'
        },
        'gu': {
            'title': 'PRAJNA PATH',
            'subtitle': 'તમારી વ્યક્તિગત માનસિક સ્વાસ્થ્ય યાત્રા',
            'name': 'નામ',
            'age': 'ઉંમર',
            'profession': 'વ્યવસાય',
            'date': 'તારીખ',
            'disclaimer': 'Disclaimer: This report is for informational purposes only and does not replace professional medical advice.',
            'page': 'પાનું',
            'no_data': 'આ વિભાગ માટે કોઈ ચોક્કસ સલાહ મળી નથી. કૃપા કરી નિષ્ણાતની સલાહ લો.',
            'main symptoms': 'મુખ્ય લક્ષણો',
            'myths': 'ભ્રમિત ખ્યાલો',
            'routine': 'દૈનિક દિનચર્યા',
            'social': 'સામાજિક પ્રવૃત્તિઓ',
            'food': 'ખોરાકની આદતો',
            'exercise': 'એક્સરસાઈઝ',
            'general': 'સામાન્ય'
        }
    }

    def get_pdf_text(key, lang='en'):
        return PDF_TRANSLATIONS.get(lang, PDF_TRANSLATIONS['en']).get(key, key)

    def localize_text(text, lang):
        """
        Filters text to show only the selected language part.
        """
        if not text:
            return ""

        # Dictionary Lookup
        text_lower = text.lower().strip()
        translations = PDF_TRANSLATIONS.get(lang, {})
        
        if text_lower in translations:
            return translations[text_lower]
        
        en_keys = PDF_TRANSLATIONS['en']
        found_key = None
        for k, v in en_keys.items():
            if v.lower() == text_lower or k == text_lower:
                found_key = k
                break
                
        if found_key and found_key in translations:
            return translations[found_key]

        # Delimiter Processing
        if '|' in text:
            parts = [p.strip() for p in text.split('|')]
            if lang == 'hi':
                return parts[1] if len(parts) > 1 else parts[0]
            
            main_part = parts[0]
            if lang == 'en':
                match = re.search(r'\((.*?)\)', main_part)
                return match.group(1) if match else main_part
            if lang == 'gu':
                return re.sub(r'\(.*?\)', '', main_part).strip()

        if '/' in text:
            parts = [p.strip() for p in text.split('/')]
            if lang == 'hi':
                return parts[-1] if len(parts) > 1 else parts[0]
            if lang == 'en':
                if len(parts) >= 3: return parts[1]
                match = re.search(r'\((.*?)\)', parts[0])
                if match: return match.group(1)
                return parts[-1] if len(parts) == 2 else parts[0]
            if lang == 'gu':
                return re.sub(r'\(.*?\)', '', parts[0]).strip()

        if ' – ' in text:
            parts = [p.strip() for p in text.split(' – ')]
            if lang == 'en': return parts[0]
            if lang == 'gu': return parts[1]
            if lang == 'hi': return parts[0]

        return text

    def detect_text_language(text):
        """Detect if text is primarily Gujarati, Hindi, or English"""
        if not text:
            return 'en'
        
        gujarati_count = sum(1 for char in text if '\u0A80' <= char <= '\u0AFF')
        hindi_count = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        latin_count = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        
        total_chars = gujarati_count + hindi_count + latin_count
        if total_chars == 0:
            return 'en'
        
        if gujarati_count > hindi_count and gujarati_count > latin_count:
            return 'gu'
        elif hindi_count > gujarati_count and hindi_count > latin_count:
            return 'hi'
        else:
            return 'en'

    def extract_advice_from_docx(upload_folder, symptoms, lang='en'):
        """
        Scans the latest uploaded docx file and extracts content ONLY in the selected language.
        Returns a dict: { 'Display Title': [ {'subtitle': 'Subheader', 'content': ['lines']} ] }
        """
        files = [f for f in os.listdir(upload_folder) if f.endswith('.docx')]
        if not files:
            return {"General": [{"subtitle": "Error", "content": ["No advice files found."]}]}
        
        latest_file = max([os.path.join(upload_folder, f) for f in files], key=os.path.getctime)
        
        # Symptom keywords for matching topics
        symptom_keywords = {
            'gad': ['anxiety', 'gad', 'ચિંતા', 'चिंता'],
            'depression': ['depression', 'ડિપ્રેશન', 'डिप्रेशन', 'उदासी'],
            'stress': ['stress', 'burnout', 'તણાવ', 'तनाव'],
            'ocd': ['ocd', 'obsessive', 'compulsive', 'બળજબરી', 'ઓસીડી', 'ओसीडी'],
            'ptsd': ['ptsd', 'trauma', 'આઘાત', 'पीटीएसडी'],
            'personality': ['personality', 'વ્યક્તિત્વ', 'व्यक्तित्व'],
            'adhd': ['adhd', 'attention', 'એડીએચડી', 'एडीएचडी'],
            'autism': ['autism', 'ઓટિઝમ', 'ऑटिज्म'],
            'eating': ['eating', 'food disorder', 'ખોરાક', 'ईटिंग']
        }
        
        # Localized display names
        display_names_localized = {
            'en': {
                'gad': 'GENERALIZED ANXIETY (GAD)',
                'depression': 'DEPRESSION',
                'stress': 'STRESS & BURNOUT',
                'ocd': 'OBSESSIVE-COMPULSIVE (OCD)',
                'ptsd': 'POST-TRAUMATIC STRESS (PTSD)',
                'personality': 'PERSONALITY IMBALANCE',
                'adhd': 'ADHD',
                'autism': 'AUTISM SPECTRUM',
                'eating': 'EATING DISORDERS'
            },
            'gu': {
                'gad': 'ચિંતાનો રોગ (GAD)',
                'depression': 'ડિપ્રેશન',
                'stress': 'તણાવ અને થાક',
                'ocd': 'ઓસીડી (OCD)',
                'ptsd': 'પીટીએસડી (PTSD)',
                'personality': 'વ્યક્તિત્વ અસંતુલન',
                'adhd': 'એડીએચડી (ADHD)',
                'autism': 'ઓટિઝમ',
                'eating': 'ખાવાની આદતોની સમસ્યાઓ'
            },
            'hi': {
                'gad': 'सामान्यीकृत चिंता विकार (GAD)',
                'depression': 'अवसाद (Depression)',
                'stress': 'तनाव और बर्नआउट',
                'ocd': 'जुनून-बाध्यकारी विकार (OCD)',
                'ptsd': 'पोस्ट-ट्रॉमैटिक स्ट्रेस (PTSD)',
                'personality': 'व्यक्तित्व असंतुलन',
                'adhd': 'एडीएचडी (ADHD)',
                'autism': 'ऑटिज़्म स्पेक्ट्रम',
                'eating': 'खाने के विकार'
            }
        }
        
        # Section header keywords
        section_headers = {
            'en': {
                'social': ['social activity', 'social activities'],
                'exercise': ['exercise', 'physical activity'],
                'food': ['food habits', 'diet', 'nutrition'],
                'routine': ['routine', 'daily routine', 'mental techniques'],
                'symptoms': ['main symptoms', 'symptoms'],
                'myths': ['myths', 'misconceptions'],
                'general': ['general']
            },
            'gu': {
                'social': ['સોશિયલ એક્ટિવિટી', 'સામાજિક પ્રવૃત્તિઓ'],
                'exercise': ['એક્સરસાઈઝ', 'વ્યાયામ'],
                'food': ['ફૂડ હેબિટ્સ', 'ખોરાકની આદતો'],
                'routine': ['રૂટિન', 'દિનચર્યા', 'મનની ટેક્નિક્સ'],
                'symptoms': ['મુખ્ય લક્ષણો', 'લક્ષણો'],
                'myths': ['ભ્રમિત ખ્યાલો', 'ભ્રામક'],
                'general': ['સામાન્ય']
            },
            'hi': {
                'social': ['सामाजिक गतिविधियाँ', 'सामाजिक'],
                'exercise': ['व्यायाम', 'एक्सरसाइज'],
                'food': ['भोजन की आदतें', 'आहार'],
                'routine': ['दिनचर्या', 'दैनिक'],
                'symptoms': ['मुख्य लक्षण', 'लक्षण'],
                'myths': ['भ्रामक धारणाएं', 'मिथक'],
                'general': ['सामान्य']
            }
        }

        advice_structure = {}
        
        try:
            doc = Document(latest_file)
            user_symptoms = [s.strip() for s in symptoms.split(',') if s.strip()]
            
            # Get main symptom categories
            main_symptoms = set()
            for sym in user_symptoms:
                main_sym = sym.split('_')[0] if '_' in sym else sym
                if main_sym in symptom_keywords:
                    main_symptoms.add(main_sym)
            
            if not main_symptoms:
                return advice_structure

            # Process each symptom
            for symptom_id in main_symptoms:
                keywords = symptom_keywords.get(symptom_id, [symptom_id])
                display_title = display_names_localized.get(lang, {}).get(symptom_id, symptom_id.upper())
                
                advice_structure[display_title] = []
                
                capturing = False
                current_lang_section = None
                current_subtopic = None
                seen_sections = {}
                
                for para in doc.paragraphs:
                    text = para.text.strip()
                    if not text:
                        continue
                    
                    text_lower = text.lower()
                    detected_lang = detect_text_language(text)
                    
                    # Check if this is a main topic header
                    is_topic_match = any(keyword in text_lower for keyword in keywords)
                    
                    # Check if this matches a DIFFERENT disorder
                    is_other_disorder = False
                    if len(text) < 150:
                        for other_id, other_keywords in symptom_keywords.items():
                            if other_id != symptom_id:
                                if any(kw in text_lower for kw in other_keywords):
                                    is_other_disorder = True
                                    break
                    
                    if is_topic_match and len(text) < 150:
                        if detected_lang == lang:
                            capturing = True
                            current_lang_section = lang
                            current_subtopic = None
                            seen_sections = {}
                        elif capturing and detected_lang != lang:
                            if current_subtopic and current_subtopic.get('content'):
                                advice_structure[display_title].append(current_subtopic)
                            capturing = False
                            current_lang_section = None
                        continue
                    
                    if capturing and is_other_disorder:
                        if current_subtopic and current_subtopic.get('content'):
                            advice_structure[display_title].append(current_subtopic)
                        capturing = False
                        current_lang_section = None
                        continue
                    
                    if capturing and current_lang_section == lang:
                        is_section_header = False
                        section_key_found = None
                        
                        for section_key, header_variants in section_headers.get(lang, {}).items():
                            if any(header.lower() in text_lower for header in header_variants):
                                is_section_header = True
                                section_key_found = section_key
                                break
                        
                        if not is_section_header and len(text) < 100:
                            clean_header = re.sub(r'^\d+\.\s*', '', text).strip()
                            for section_key, header_variants in section_headers.get(lang, {}).items():
                                if any(header.lower() in clean_header.lower() for header in header_variants):
                                    is_section_header = True
                                    section_key_found = section_key
                                    break
                        
                        if is_section_header and section_key_found:
                            if current_subtopic and current_subtopic.get('content'):
                                standardized_name = get_pdf_text(section_key_found, lang) or text
                                if standardized_name in seen_sections:
                                    seen_sections[standardized_name]['content'].extend(current_subtopic['content'])
                                else:
                                    advice_structure[display_title].append(current_subtopic)
                                    seen_sections[current_subtopic['subtitle']] = current_subtopic
                            
                            standardized_name = get_pdf_text(section_key_found, lang) or text
                            
                            if standardized_name in seen_sections:
                                current_subtopic = seen_sections[standardized_name]
                            else:
                                current_subtopic = {'subtitle': standardized_name, 'content': [], 'section_type': section_key_found}
                                seen_sections[standardized_name] = current_subtopic
                        else:
                            if detected_lang == lang:
                                clean_text = text.lstrip('-•').strip()
                                if clean_text and len(clean_text) > 3:
                                    if current_subtopic is None:
                                        general_title = get_pdf_text('general', lang)
                                        current_subtopic = {'subtitle': general_title, 'content': [], 'section_type': 'general'}
                                        seen_sections[general_title] = current_subtopic
                                    current_subtopic['content'].append(clean_text)
                
                if current_subtopic and current_subtopic.get('content'):
                    if current_subtopic not in advice_structure[display_title]:
                        advice_structure[display_title].append(current_subtopic)
                
                # Deduplicate
                unique_sections = []
                seen_titles = set()
                for section in advice_structure[display_title]:
                    if section['subtitle'] not in seen_titles:
                        unique_sections.append(section)
                        seen_titles.add(section['subtitle'])
                
                advice_structure[display_title] = unique_sections
                
                if not advice_structure[display_title]:
                    del advice_structure[display_title]

        except Exception as e:
            return {"Error": [{"subtitle": "Error", "content": [f"Error reading doc: {str(e)}"]}]}
            
        return advice_structure


    def create_pdf_report(user_session, advice_data):
        """
        Create a PDF report matching the design from the uploaded image
        """
        lang = getattr(user_session, 'language', 'en')
        
        # Register fonts
        try:
            if os.path.exists(FONT_PATH_NIRMALA):
                pdfmetrics.registerFont(TTFont('Nirmala', FONT_PATH_NIRMALA))
        except:
            pass
        
        filename = f"report_{user_session.id}.pdf"
        path = os.path.join("static", filename)
        
        # Create PDF
        doc = SimpleDocTemplate(
            path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=60,
            bottomMargin=60
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Title style (PRAJNA PATH)
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=32,
            textColor=colors.HexColor('#5D4037'),  # Brown color
            alignment=TA_CENTER,
            spaceAfter=10,
            spaceBefore=20
        )
        
        # Subtitle style
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # Section header style (for disorder names like PTSD, OCD)
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=colors.HexColor('#5D4037'),
            spaceAfter=8,
            spaceBefore=15
        )
        
        # Subsection style (General, Exercise, etc.)
        subsection_style = ParagraphStyle(
            'Subsection',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=13,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=8
        )
        
        # Body text style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.black,
            leading=14,
            leftIndent=15,
            spaceAfter=4
        )
        
        # Add title
        title = Paragraph(get_pdf_text('title', lang), title_style)
        elements.append(title)
        
        # Add subtitle
        subtitle = Paragraph(get_pdf_text('subtitle', lang), subtitle_style)
        elements.append(subtitle)
        
        # Add user details in a table (always in English)
        user_data = [
            ["Name:", str(user_session.name), 
            "Age:", str(user_session.age)],
            ["Profession:", str(user_session.profession),
            "Date:", datetime.now().strftime('%Y-%m-%d')]
        ]
        
        user_table = Table(user_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch])
        user_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#666666')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(user_table)
        elements.append(Spacer(1, 20))
        
        # Color scheme for different sections
        section_colors = {
            'general': colors.HexColor('#F5DEB3'),      # Wheat/Tan
            'exercise': colors.HexColor('#B0C4DE'),     # Light Steel Blue
            'food': colors.HexColor('#FFD4A3'),         # Peach
            'routine': colors.HexColor('#D4E7D4'),      # Light Green
            'social': colors.HexColor('#E6D5E6'),       # Lavender
            'symptoms': colors.HexColor('#FFE4B5'),     # Moccasin
            'myths': colors.HexColor('#F0E68C')         # Khaki
        }
        
        # Process advice data
        for disorder_name, sections in advice_data.items():
            # Add disorder name as section header
            section_header = Paragraph(disorder_name, section_header_style)
            elements.append(section_header)
            
            for section in sections:
                subtitle = section.get('subtitle', '')
                content_list = section.get('content', [])
                section_type = section.get('section_type', 'general')
                
                if not content_list:
                    continue
                
                # Get color for this section type
                bg_color = section_colors.get(section_type, colors.HexColor('#F5F5F5'))
                
                # Create content for the colored box
                box_content = []
                
                # Add subtitle
                if subtitle:
                    subsection_para = Paragraph(f"<b>{subtitle}</b>", subsection_style)
                    box_content.append([subsection_para])
                
                # Add content items as bullets
                for item in content_list:
                    # Clean the item
                    clean_item = item.strip()
                    if clean_item:
                        bullet_text = f"• {clean_item}"
                        bullet_para = Paragraph(bullet_text, body_style)
                        box_content.append([bullet_para])
                
                # Create table for colored box
                if box_content:
                    content_table = Table(box_content, colWidths=[6.5*inch])
                    content_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 15),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    
                    elements.append(content_table)
                    elements.append(Spacer(1, 15))
            
            elements.append(Spacer(1, 10))
        
        # Add disclaimer at the bottom
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        elements.append(Spacer(1, 20))
        disclaimer = Paragraph(get_pdf_text('disclaimer', lang), disclaimer_style)
        elements.append(disclaimer)
        
        # Build PDF
        doc.build(elements)
        
        return path
