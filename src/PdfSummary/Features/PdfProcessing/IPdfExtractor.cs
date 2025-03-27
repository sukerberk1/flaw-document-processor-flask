using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;

namespace PdfSummary.Features.PdfProcessing
{
    public interface IPdfExtractor
    {
        Task<string> ExtractTextFromPdfAsync(IFormFile pdfFile);
    }
}
