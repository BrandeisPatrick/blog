You are given a spreadsheet manipulation request from a real user,
plus three test-case workbooks: 1_input.xlsx, 2_input.xlsx, 3_input.xlsx
(same structure, different data).

Apply the request to EACH input workbook and save the results as
1_output.xlsx, 2_output.xlsx, 3_output.xlsx in the working directory.
Python with openpyxl is available at .venv/bin/python. Compute final VALUES
in the answer cells (formulas are also acceptable only if openpyxl would
show cached values; when in doubt, write computed values).

Do not modify the input files. Answers will be checked at position: K3:K10

<request>
How can I create a formula in Excel that assigns a unique code number (UCODENUMBER) to each different combination of product features? Each product is defined by three features -- NCM, Manufacturer, and Country -- and when the exact same features are present, they should have the same UCODENUMBER. The first unique combination should be numbered as 1, and subsequent combinations should be numbered sequentially. If a combination repeats, it should receive the original number assigned. Ideally, the solution should avoid intermediate steps such as concatenation, strive to use a single formula, and the formula should handle everything in one step if possible.
I have different products (A,B,C etc..) , all product are defined by 3 features (NCM, MANUFACTURER,COUNTRY)

the combination of those 3 features give a UCODE , if the product have the exact same features they will all have the same UCODE , if not it will generate a different code. UCODE is obtained by concatenating (NCM & Manufacturer & ORIGIN)

UCODENUMBER is the result I would like to obtain using a single formula, could be an array formula but I would like the least possible step ( if we can get rid of the concatenation part would be even nicer)

UCODENUMBER will always be 1 for the first ucode then if the next ucode is the same it remain 1, if the following ucode is different it will be 2, and if the following is the same as the first it will be 1 again.
Basically it count all different UCODE , if some UCODE are the same they will be under the same UCODENUMBER

I found a solution using Concatenation + an array which count all the different UCODE + and index match that return the corresponding number (1,2,3 etc)
INDEX(NUMERO,MATCH(J3,UNICODE,0),2)
</request>
