using System.Threading.Tasks;

namespace PdfSummary.Features.PdfProcessing
{
    public interface IPdfSummarizer
    {
        Task<string> SummarizeTextAsync(string text);
    }
}
