from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine, LTTextBox

def extract_text_from_pdf(filename, page_numbers=None, min_line_length=1):
    '''从PDF文件中（按指定页码）提取文本内容'''
    paragrahs = []
    buffer = ''
    full_text = ''

    # 提取全部文本内容
    for i, page_layout in enumerate(extract_pages(filename)):
        # 如果指定了页码，只处理指定页码的内容
        if page_numbers and i not in page_numbers:
            continue
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                full_text += element.get_text() + '\n'

    # 安空行分隔，将文本重新组成段落
    lines = full_text.split('\n')
    for text in lines:
        if len(text) >= min_line_length:
            buffer += (' ' + text) if not text.endswith('-') else text.strip('-')
        elif buffer:
            paragrahs.append(buffer)
            buffer = ''
    if buffer:
        paragrahs.append(buffer)
    return paragrahs

if __name__ == '__main__':
    filename = 'sample.pdf'
    paragrahs = extract_text_from_pdf(filename, page_numbers=[9, 10], min_line_length=10)
    for i, p in enumerate(paragrahs):
        print(f'{i+1}: {p}')        



