from google import genai

client = genai.Client(api_key="")

def csv2html(cvs):
  prompt = f"""

  You are a data processing assistant specializing in converting CSV files to HTML format.
  I will provide you with the contents of a CSV file, and your task is to convert it into an HTML table format.
  The CSV content is as follows:
  {cvs}
  Please return the HTML table representation of the CSV content.

  Points to consider:
  1. You have to return the HTML table representation of the CSV content.
  2. Merge the cells in the HTML table if they are similar.
  3. Merge the cells in the HTML table, if you think they are meant to merged based on the CSV content.
  4. Fix the typos in the CSV content if you find any.
  5. Remember to return only the HTML table representation, nothing else.
  4. Do not return any explanation or any other text.
  5. Do not return any CSV file, only the HTML table representation.
  6. Do not return any other text, only the HTML table representation.
  """
  response = client.models.generate_content(
      model="gemini-2.0-flash", contents = prompt
  )
  html = response.text.replace("'", "").replace('"', '')
  html = html.replace("`", "")
  html = '<table' + html.split('<table')[1]
  html = html.replace('\n', '')
  return html