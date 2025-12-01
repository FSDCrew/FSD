import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, Minus } from "lucide-react";
import { format } from "date-fns";
import type { RequiredInputField } from "@/lib/api/crew";

interface KickoffFormProps {
  requiredInputs: RequiredInputField[];
  dynamicFormData: Record<string, any>;
  orshotSchemaFields: Array<{field: string, dataType: string, description: string}>;
  onFormChange: (fieldName: string, value: any) => void;
  onOrshotSchemaChange: (fields: Array<{field: string, dataType: string, description: string}>) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export function KickoffForm({
  requiredInputs,
  dynamicFormData,
  orshotSchemaFields,
  onFormChange,
  onOrshotSchemaChange,
  onSubmit,
}: KickoffFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {requiredInputs.map((field) => {
        const typeInfo = field.type_info as any;
        
        // Handle orshot_schema
        if (field.field_name === "orshot_schema" && typeInfo.is_list) {
          return (
            <div key={field.field_name} className="space-y-3">
              <Label>
                {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              {orshotSchemaFields.map((schemaField, index) => (
                <div key={index} className="flex gap-2 items-start">
                  <div className="flex-1">
                    <Label className="text-xs">Field</Label>
                    <Input
                      placeholder="e.g., headline"
                      value={schemaField.field}
                      onChange={(e) => {
                        const newFields = [...orshotSchemaFields];
                        newFields[index].field = e.target.value;
                        onOrshotSchemaChange(newFields);
                      }}
                    />
                  </div>
                  <div className="w-[160px]">
                    <Label className="text-xs">Data Type</Label>
                    <Select
                      value={schemaField.dataType}
                      onValueChange={(value) => {
                        const newFields = [...orshotSchemaFields];
                        newFields[index].dataType = value;
                        onOrshotSchemaChange(newFields);
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="TEXT">TEXT</SelectItem>
                        <SelectItem value="IMAGE">IMAGE</SelectItem>
                        <SelectItem value="BACKGROUND">BACKGROUND</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex-1">
                    <Label className="text-xs">Description</Label>
                    <Textarea
                      placeholder="e.g., Main title"
                      value={schemaField.description}
                      onChange={(e) => {
                        const newFields = [...orshotSchemaFields];
                        newFields[index].description = e.target.value;
                        onOrshotSchemaChange(newFields);
                      }}
                      rows={3}
                      className="resize-y"
                    />
                  </div>
                  <div className="flex items-center pt-6">
                    <Button
                      type="button"
                      variant="destructive"
                      size="icon"
                      className={`h-8 w-8 rounded-full flex-shrink-0 bg-gray-600 ${index === 0 ? 'invisible' : ''}`}
                      onClick={() => {
                        const newFields = orshotSchemaFields.filter((_, i) => i !== index);
                        onOrshotSchemaChange(newFields);
                      }}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  onOrshotSchemaChange([...orshotSchemaFields, {field: "", dataType: "", description: ""}]);
                }}
              >
                + Add Row
              </Button>
            </div>
          );
        }
        
        // Handle enum fields
        if (typeInfo.is_enum && typeInfo.enum_values) {
          if (typeInfo.is_list) {
            const selectedValues = dynamicFormData[field.field_name] || [];
            
            return (
              <div key={field.field_name} className="space-y-2">
                <Label>
                  {field.field_name === "templateId" 
                    ? "Template Id" 
                    : field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                  {field.required && <span className="text-red-500 ml-1">*</span>}
                </Label>
                <div className="flex flex-wrap gap-2">
                  {typeInfo.enum_values.map((value: any) => {
                    const isSelected = selectedValues.includes(value);
                    return (
                      <Button
                        key={String(value)}
                        type="button"
                        variant={isSelected ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          const newValues = isSelected
                            ? selectedValues.filter((v: any) => v !== value)
                            : [...selectedValues, value];
                          onFormChange(field.field_name, newValues);
                        }}
                      >
                        {String(value)}
                      </Button>
                    );
                  })}
                </div>
                {selectedValues.length > 0 && (
                  <div className="text-sm text-muted-foreground">
                    Selected: {selectedValues.join(", ")}
                  </div>
                )}
              </div>
            );
          }
          
          return (
            <div key={field.field_name} className="space-y-2">
              <Label>
                {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <Select
                value={dynamicFormData[field.field_name] ? String(dynamicFormData[field.field_name]) : ""}
                onValueChange={(value) => onFormChange(field.field_name, value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={field.placeholder || `Select ${field.field_name}`} />
                </SelectTrigger>
                <SelectContent>
                  {typeInfo.enum_values.map((value: any) => (
                    <SelectItem key={String(value)} value={String(value)}>
                      {String(value)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          );
        }
        
        // Handle date fields
        if (typeInfo.type === 'date' || field.field_name.includes('date')) {
          return (
            <div key={field.field_name} className="space-y-2">
              <Label>
                {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={`w-full justify-start text-left font-normal ${
                      !dynamicFormData[field.field_name] && "text-muted-foreground"
                    }`}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {dynamicFormData[field.field_name] ? (
                      format(new Date(dynamicFormData[field.field_name]), "PPP")
                    ) : (
                      <span>Select date</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={dynamicFormData[field.field_name] ? new Date(dynamicFormData[field.field_name]) : undefined}
                    onSelect={(date) => {
                      if (date) {
                        onFormChange(field.field_name, date.toISOString());
                      }
                    }}
                    captionLayout="dropdown"
                    fromYear={2020}
                    toYear={2030}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
          );
        }
        
        // Handle basic string fields
        return (
          <div key={field.field_name} className="space-y-2">
            <Label>
              {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Textarea
              placeholder={field.placeholder || `Enter ${field.field_name}`}
              value={dynamicFormData[field.field_name] || ""}
              onChange={(e) => onFormChange(field.field_name, e.target.value)}
              rows={3}
            />
          </div>
        );
      })}
    </form>
  );
}
