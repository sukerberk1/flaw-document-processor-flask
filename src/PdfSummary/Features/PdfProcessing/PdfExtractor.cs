using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;

namespace PdfSummary.Features.PdfProcessing
{
    public class PdfExtractor : IPdfExtractor
    {
        public async Task<string> ExtractTextFromPdfAsync(IFormFile pdfFile)
        {
            if (pdfFile == null || pdfFile.Length == 0)
                throw new ArgumentException("No file was uploaded");

            using var memoryStream = new MemoryStream();
            await pdfFile.CopyToAsync(memoryStream);
            memoryStream.Position = 0;

            var extractedText = new System.Text.StringBuilder();
            
            using (var document = PdfDocument.Open(memoryStream))
            {
                foreach (var page in document.GetPages())
                {
                    extractedText.AppendLine(page.Text);
                }
            }

            return extractedText.ToString();
        }
    }
}
