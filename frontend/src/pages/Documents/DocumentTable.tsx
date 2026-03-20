import React, { useState, useEffect } from 'react';
import {
  Table,
  Tag,
  Button,
  Space,
  Input,
  Select,
  message,
  Tooltip,
  Popconfirm,
} from 'antd';
import {
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  SearchOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getDocuments, deleteDocument } from '@/services/documentService';
import type { DocumentInfo } from '@/types/document';
import EmptyState from '@/components/common/EmptyState';
import dayjs from 'dayjs';

interface DocumentTableProps {
  onUploadClick: () => void;
}

const DocumentTable: React.FC<DocumentTableProps> = ({ onUploadClick }) => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchText, setSearchText] = useState('');
  const [collectionFilter, setCollectionFilter] = useState<string>('all');

  const collections = [
    { label: '全部知识库', value: 'all' },
    { label: '默认知识库', value: 'default' },
    { label: 'HR制度文档', value: 'hr_docs' },
    { label: '产品手册', value: 'product_docs' },
    { label: '技术文档', value: 'tech_docs' },
  ];

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const collection =
        collectionFilter === 'all' ? 'default' : collectionFilter;
      const data = await getDocuments(collection, page, pageSize);
      setDocuments(data.documents);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load documents:', error);
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [page, pageSize, collectionFilter]);

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId);
      message.success('文档已删除');
      loadDocuments();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusTag = (status: DocumentInfo['status']) => {
    const statusMap: Record<DocumentInfo['status'], { color: string; text: string }> = {
      uploaded: { color: 'default', text: '已上传' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
    };
    const { color, text } = statusMap[status] || { color: 'default', text: status };
    return <Tag color={color}>{text}</Tag>;
  };

  const columns: ColumnsType<DocumentInfo> = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename: string, record) => (
        <div className="flex items-center gap-2">
          <FileTextOutlined className="text-blue-500" />
          <div>
            <div className="font-medium">{filename}</div>
            <div className="text-xs text-gray-400">
              {record.file_type.toUpperCase()} · {formatFileSize(record.file_size)}
            </div>
          </div>
        </div>
      ),
    },
    {
      title: '知识库',
      dataIndex: 'collection',
      key: 'collection',
      width: 120,
      render: (collection: string) => {
        const collectionMap: Record<string, string> = {
          default: '默认',
          hr_docs: 'HR文档',
          product_docs: '产品手册',
          tech_docs: '技术文档',
        };
        return <Tag>{collectionMap[collection] || collection}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: getStatusTag,
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 100,
      render: (count?: number) => count ?? '-',
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              disabled={record.status !== 'completed'}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个文档吗？"
            description="删除后无法恢复，相关知识将被移除"
            onConfirm={() => handleDelete(record.doc_id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 过滤搜索结果
  const filteredDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchText.toLowerCase())
  );

  if (total === 0 && !loading) {
    return (
      <EmptyState
        type="documents"
        title="暂无文档"
        description="上传文档以开始构建知识库"
        actionText="上传文档"
        onAction={onUploadClick}
      />
    );
  }

  return (
    <div>
      {/* 筛选栏 */}
      <div className="flex items-center justify-between mb-4 gap-4">
        <Input
          prefix={<SearchOutlined className="text-gray-400" />}
          placeholder="搜索文档..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 240 }}
        />
        <Select
          value={collectionFilter}
          onChange={setCollectionFilter}
          options={collections}
          style={{ width: 150 }}
          suffixIcon={<FilterOutlined />}
        />
      </div>

      {/* 表格 */}
      <Table
        columns={columns}
        dataSource={filteredDocuments}
        rowKey="doc_id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (p, ps) => {
            setPage(p);
            setPageSize(ps);
          },
        }}
      />
    </div>
  );
};

export default DocumentTable;
