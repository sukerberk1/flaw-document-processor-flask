using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using PdfSummary.Features.PdfProcessing;

namespace PdfSummary.Features.PdfSummary
{
    [ApiController]
    [Route("api/[controller]")]
    public class PdfSummaryController : ControllerBase
    {
        private readonly IPdfExtractor _pdfExtractor;
        private readonly IPdfSummarizer _pdfSummarizer;

        public PdfSummaryController(IPdfExtractor pdfExtractor, IPdfSummarizer pdfSummarizer)
        {
            _pdfExtractor = pdfExtractor;
            _pdfSummarizer = pdfSummarizer;
        }

        [HttpPost]
        public async Task<IActionResult> SummarizePdf(IFormFile file)
        {
            try
            {
                if (file == null || file.Length == 0)
                    return BadRequest("No file uploaded");

                if (!file.ContentType.Equals("application/pdf", StringComparison.OrdinalIgnoreCase))
                    return BadRequest("Only PDF files are supported");

                // Extract text from PDF
                var extractedText = await _pdfExtractor.ExtractTextFromPdfAsync(file);
                
                // Generate summary
                var summary = await _pdfSummarizer.SummarizeTextAsync(extractedText);

                return Ok(new { summary });
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"An error occurred: {ex.Message}");
            }
        }
    }
}
