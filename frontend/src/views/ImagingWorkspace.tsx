import React, { useState } from 'react';
import {
  Upload,
  ImageIcon,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  FileImage,
  Eye,
  Info,
  ShieldAlert,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { UncertaintyBadge, Badge } from '../components/ui/Badge';
import { VisionAnalysisResponse } from '../types/clinical';
import { api } from '../api/client';

interface ImagingWorkspaceProps {
  activeImagePath: string | null;
  onSelectImage: (path: string | null) => void;
  onAttachToPatient: (path: string) => void;
}

export const ImagingWorkspace: React.FC<ImagingWorkspaceProps> = ({
  activeImagePath,
  onSelectImage,
  onAttachToPatient,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [visionResult, setVisionResult] = useState<VisionAnalysisResponse | null>(null);
  const [currentFile, setCurrentFile] = useState<File | null>(null);

  // File upload handler
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      setUploadError('Invalid file type. Only standard PNG, JPG, or JPEG radiographic images are accepted.');
      return;
    }

    // Validate size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File exceeds 10MB limit. Please upload a compressed or standard radiographic export.');
      return;
    }

    setUploadError(null);
    setCurrentFile(file);
    setIsUploading(true);

    try {
      const res = await api.uploadImage(file);
      if (res.success && res.image_path) {
        onSelectImage(res.image_path);
        onAttachToPatient(res.image_path);
      }
    } catch (err: any) {
      setUploadError(err.message || 'Image upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  // Attach synthetic demo chest X-ray
  const handleAttachDemo = () => {
    const demoPath = 'data/demo/demo_chest_xray.png';
    onSelectImage(demoPath);
    onAttachToPatient(demoPath);
    setUploadError(null);
    setCurrentFile(null);
  };

  // Run standalone vision analysis
  const handleAnalyzeImage = async () => {
    if (!activeImagePath) return;
    setIsAnalyzing(true);
    setUploadError(null);

    try {
      let fileToAnalyze = currentFile;
      if (!fileToAnalyze) {
        // Fetch demo image as blob to send to endpoint
        const cleanPath = activeImagePath.replace(/^\.?\/?/, '');
        const blobRes = await fetch(`/${cleanPath}`);
        const blob = await blobRes.blob();
        fileToAnalyze = new File([blob], 'demo_chest_xray.png', { type: 'image/png' });
      }

      const res = await api.analyzeImage(fileToAnalyze);
      setVisionResult(res);
    } catch (err: any) {
      setUploadError(err.message || 'Radiology vision analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Image source path formatting for browser preview
  const displaySrc = activeImagePath
    ? `/${activeImagePath.replace(/^\.?\/?/, '')}`
    : null;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-teal-700" />
            Radiology Imaging Workstation
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Standard 2D radiographic inspection, format verification, and specialized medical vision analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant="outline"
            leftIcon={<Sparkles className="w-4 h-4 text-teal-600" />}
            onClick={handleAttachDemo}
          >
            Attach Synthetic Demo CXR
          </Button>

          {activeImagePath && (
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Eye className="w-4 h-4" />}
              isLoading={isAnalyzing}
              onClick={handleAnalyzeImage}
            >
              Analyze Radiograph
            </Button>
          )}
        </div>
      </div>

      {uploadError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs px-4 py-3 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{uploadError}</span>
          </div>
          <button onClick={() => setUploadError(null)} className="text-rose-700 font-bold">
            ×
          </button>
        </div>
      )}

      {/* Main Split Layout: Viewer on Left, Findings on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Viewer & Dropzone (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card
            title={
              <div className="flex items-center justify-between w-full">
                <span className="font-semibold text-slate-800">Radiographic Scan Viewer</span>
                <span className="text-[11px] text-slate-400 font-normal">
                  Modality: Chest Radiograph (CXR)
                </span>
              </div>
            }
            bodyClassName="p-0"
          >
            {/* Viewer Screen with dark clinical backdrop */}
            <div className="relative bg-slate-950 min-h-[440px] flex items-center justify-center p-4 overflow-hidden rounded-b-xl select-none">
              {displaySrc ? (
                <div
                  className="transition-transform duration-200 flex items-center justify-center"
                  style={{ transform: `scale(${zoomLevel / 100})` }}
                >
                  <img
                    src={displaySrc}
                    alt="Active Radiograph"
                    className="max-h-[420px] w-auto object-contain rounded shadow-lg border border-slate-800"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                </div>
              ) : (
                <div className="text-center text-slate-500 space-y-3 p-8">
                  <FileImage className="w-12 h-12 mx-auto text-slate-700" />
                  <p className="text-sm font-medium text-slate-400">No Radiographic Image Loaded</p>
                  <p className="text-xs text-slate-600 max-w-xs mx-auto">
                    Upload a patient chest radiograph or load the synthetic educational demo scan to begin inspection.
                  </p>
                </div>
              )}

              {/* Viewer Controls Overlay */}
              {displaySrc && (
                <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur-xs border border-slate-700/80 rounded-lg p-1.5 flex items-center gap-1 text-slate-300">
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(50, z - 25))}
                    className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="text-xs font-mono px-2 text-slate-400">{zoomLevel}%</span>
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(250, z + 25))}
                    className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setZoomLevel(100)}
                    className="p-1.5 hover:text-white hover:bg-slate-800 rounded transition-colors"
                    title="Reset Zoom"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          </Card>

          {/* Upload Dropzone */}
          <div className="bg-white rounded-xl border border-dashed border-slate-300 p-5 text-center hover:border-teal-500 transition-colors">
            <input
              type="file"
              id="cxr-upload"
              accept=".png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="cxr-upload" className="cursor-pointer flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-teal-50 text-teal-700 flex items-center justify-center">
                <Upload className="w-5 h-5" />
              </div>
              <span className="text-sm font-semibold text-slate-800">
                {isUploading ? 'Uploading & Sanity Checking Image...' : 'Click to Upload Radiograph'}
              </span>
              <span className="text-xs text-slate-400">
                Supports standard PNG, JPG, or JPEG up to 10MB. Non-DICOM web viewer.
              </span>
            </label>
          </div>
        </div>

        {/* Right Column: Metadata & Vision Findings (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Metadata Card */}
          <Card title="Image Metadata & Acquisition">
            <div className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">File Identifier:</span>
                <span className="font-mono text-slate-800 font-medium truncate max-w-xs">
                  {activeImagePath ? activeImagePath.split(/[/\\]/).pop() : 'None'}
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Modality:</span>
                <span className="font-medium text-slate-800">Plain Film Radiography</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">DICOM Compliance:</span>
                <span className="text-slate-500 font-medium">Standard Web Export (RGB/PNG)</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-500">Attachment Status:</span>
                <Badge variant={activeImagePath ? 'teal' : 'neutral'}>
                  {activeImagePath ? 'Attached to Current Patient' : 'Unattached'}
                </Badge>
              </div>
            </div>
          </Card>

          {/* Structured Vision Findings Card */}
          <Card
            title="Radiological Vision Analysis"
            subtitle="Extracted visual findings and anatomical features"
          >
            {!visionResult ? (
              <div className="p-8 text-center text-xs text-slate-400 space-y-2">
                <Eye className="w-6 h-6 mx-auto text-slate-300" />
                <p>No standalone vision analysis executed yet.</p>
                <p className="text-[11px] text-slate-400">
                  Click "Analyze Radiograph" above or run the full Multi-Agent analysis to evaluate findings.
                </p>
              </div>
            ) : !visionResult.success ? (
              <div className="p-4 bg-rose-50 text-rose-800 rounded-lg text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>Analysis error: {visionResult.error || 'Failed to analyze radiograph'}</span>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Vision Telemetry */}
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Technical Quality:</span>
                    <span className="font-medium text-emerald-700 capitalize">
                      {visionResult.technical_quality}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Vision Model:</span>
                    <span className="font-mono text-slate-700">{visionResult.model_used}</span>
                  </div>
                </div>

                {/* Overall Impression */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Overall Impression:
                  </h4>
                  <p className="text-xs text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200 leading-relaxed">
                    {visionResult.overall_impression || 'No impression stated.'}
                  </p>
                </div>

                {/* Detected Features Table */}
                {visionResult.findings && visionResult.findings.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                      Detected Anatomical Findings ({visionResult.findings.length}):
                    </h4>
                    <div className="space-y-2">
                      {visionResult.findings.map((f, i) => (
                        <div
                          key={i}
                          className="p-2.5 rounded-lg border border-slate-200 bg-white text-xs space-y-1"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-900">{f.location}</span>
                            <UncertaintyBadge level={f.confidence} />
                          </div>
                          <p className="text-slate-600 text-[11px]">{f.finding}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Clinical Limitation Banner */}
          <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl text-[11px] text-amber-900 space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-amber-900">
              <ShieldAlert className="w-4 h-4 text-amber-700" />
              Model Limitations & Non-Diagnostic Notice
            </div>
            <p className="leading-relaxed text-amber-800">
              This imaging interface processes standard raster graphics (PNG/JPG) for educational correlation. It does not replace a certified PACS/DICOM viewing station and should not be used as the sole basis for acute diagnostic or therapeutic decisions.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
