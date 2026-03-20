import React, { useState, useCallback } from 'react';
import { Button, message } from 'antd';
import { UploadOutlined, ReloadOutlined } from '@ant-design/icons';
import DocumentTable from './DocumentTable';
import UploadModal from './UploadModal';
import EmptyState from '@/components/common/EmptyState';

const DocumentsPage: React.FC = () => {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    message.success('文档上传成功');
    setUploadModalOpen(false);
    setRefreshKey((k) => k + 1);
  };

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold">文档管理</h1>
          <p className="text-sm text-gray-500 mt-1">
            上传和管理知识库文档，支持 PDF、DOCX、MD、TXT 格式
          </p>
        </div>
        <div className="flex gap-2">
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setUploadModalOpen(true)}
          >
            上传文档
          </Button>
        </div>
      </div>

      {/* 文档列表 */}
      <div className="flex-1 overflow-auto">
        <DocumentTable
          key={refreshKey}
          onUploadClick={() => setUploadModalOpen(true)}
        />
      </div>

      {/* 上传弹窗 */}
      <UploadModal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={handleUploadSuccess}
      />
    </div>
  );
};

export default DocumentsPage;
