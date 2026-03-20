import React, { useState } from 'react'
import { Modal, Upload, Select, Button, Progress, message } from 'antd'
import { UploadOutlined, InboxOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { uploadDocument } from '@/services/documentService'

const { Dragger } = Upload

interface UploadModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

const UploadModal: React.FC<UploadModalProps> = ({ open, onClose, onSuccess }) => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [collection, setCollection] = useState('default')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const collections = [
    { label: '默认知识库', value: 'default' },
    { label: 'HR制度文档', value: 'hr_docs' },
    { label: '产品手册', value: 'product_docs' },
    { label: '技术文档', value: 'tech_docs' },
  ]

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请选择文件')
      return
    }

    setUploading(true)
    setProgress(0)

    try {
      // 从 fileList 中获取文件，兼容不同版本的 antd
      const uploadFile = fileList[0]
      const file = uploadFile.originFileObj || (uploadFile as unknown as File)
      if (!file || typeof file.size !== 'number') {
        throw new Error('文件不存在')
      }

      await uploadDocument(file as File, collection, setProgress)
      message.success('文档上传成功，正在后台处理...')
      setFileList([])
      onSuccess()
    } catch (error) {
      console.error('Upload error:', error)
      message.error('上传失败，请重试')
    } finally {
      setUploading(false)
      setProgress(0)
    }
  }

  const handleClose = () => {
    if (!uploading) {
      setFileList([])
      setCollection('default')
      onClose()
    }
  }

  const props = {
    name: 'file',
    multiple: false,
    fileList,
    beforeUpload: (file: File) => {
      // 检查文件类型
      const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown',
        'text/plain',
      ]
      const allowedExtensions = ['.pdf', '.docx', '.md', '.txt']

      const hasExtension = allowedExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))

      if (!hasExtension) {
        message.error('不支持的文件格式，请上传 PDF、DOCX、MD 或 TXT 文件')
        return false
      }

      // 检查文件大小 (50MB)
      if (file.size > 50 * 1024 * 1024) {
        message.error('文件大小不能超过 50MB')
        return false
      }

      setFileList([file as unknown as UploadFile])
      return false // 阻止自动上传
    },
    onRemove: () => {
      setFileList([])
    },
  }

  return (
    <Modal
      title='上传文档'
      open={open}
      onCancel={handleClose}
      footer={null}
      width={500}
      destroyOnClose
    >
      <div className='py-4'>
        {/* 知识库选择 */}
        <div className='mb-4'>
          <label className='block text-sm font-medium text-gray-700 mb-2'>知识库</label>
          <Select
            value={collection}
            onChange={setCollection}
            options={collections}
            style={{ width: '100%' }}
          />
        </div>

        {/* 文件上传 */}
        <Dragger {...props} disabled={uploading}>
          <p className='text-4xl text-gray-400 mb-4'>
            <InboxOutlined />
          </p>
          <p className='text-base text-gray-600'>点击或拖拽文件到此区域上传</p>
          <p className='text-sm text-gray-400 mt-2'>支持 PDF、DOCX、MD、TXT 格式，最大 50MB</p>
        </Dragger>

        {/* 上传进度 */}
        {uploading && (
          <div className='mt-4'>
            <Progress percent={progress} status='active' />
            <p className='text-sm text-gray-500 text-center'>正在上传...</p>
          </div>
        )}

        {/* 操作按钮 */}
        <div className='flex justify-end gap-2 mt-4'>
          <Button onClick={handleClose} disabled={uploading}>
            取消
          </Button>
          <Button
            type='primary'
            onClick={handleUpload}
            disabled={fileList.length === 0}
            loading={uploading}
          >
            上传
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export default UploadModal
