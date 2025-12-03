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
import { CalendarIcon, Minus, Plus } from "lucide-react";
import { format } from "date-fns";
import type { KickoffFormProps } from "@/types/ComponentProps";
import type { RequiredInputField } from "@/lib/api/crew";

type TypeInfo = {
  type: string;
  is_list?: boolean;
  is_enum?: boolean;
  is_custom_model?: boolean;
  inner_type?: string;
  enum_values?: any[];
  model_schema?: {
    properties?: Record<string, any>;
    required?: string[];
    $defs?: Record<string, any>;
  };
};

// Helper function to format field names
function formatFieldName(fieldName: string): string {
  return fieldName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

// Reusable enable checkbox component for nullable fields
function EnableCheckbox({
  checked,
  onChange,
  onEnable,
  label = "Enable",
}: {
  checked: boolean;
  onChange: (value: any) => void;
  onEnable: () => any;
  label?: string;
}) {
  return (
    <div className="flex items-center space-x-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => {
          if (e.target.checked) {
            onChange(onEnable());
          } else {
            onChange(null);
          }
        }}
        className="h-4 w-4"
      />
      <Label className="text-xs">{label}</Label>
    </div>
  );
}

// Helper function to check if a $ref points to an enum
function isEnumRef(ref: string, defs: Record<string, any>): boolean {
  if (!ref || !defs) return false;
  const refName = ref.replace("#/$defs/", "");
  const def = defs[refName];
  return def && def.enum !== undefined;
}

// Helper function to get enum values from $ref
function getEnumValuesFromRef(ref: string, defs: Record<string, any>): any[] {
  if (!ref || !defs) return [];
  const refName = ref.replace("#/$defs/", "");
  const def = defs[refName];
  if (def && def.enum) {
    return def.enum;
  }
  return [];
}

// Helper function to get model schema from $ref
function getModelSchemaFromRef(ref: string, defs: Record<string, any>): any {
  if (!ref || !defs) return null;
  const refName = ref.replace("#/$defs/", "");
  return defs[refName] || null;
}

// Render dynamic object with key-value pairs
function renderDynamicObject(
  propName: string,
  propSchema: any,
  value: any,
  onChange: (value: any) => void,
  required: boolean,
  defs?: Record<string, any>,
  skipLabel?: boolean
): React.ReactNode {
  const objValue = value || {};
  const isRequired = required;
  const placeholder = propSchema.description || `Enter ${propName}`;

  // Check if additionalProperties specifies a type
  const valueType = propSchema.additionalProperties?.type || "string";

  // Convert object to array of entries for stable rendering with indices
  const entries = Object.entries(objValue);
  
  // Track which fields have been touched (blurred)
  const [touchedKeys, setTouchedKeys] = React.useState<Set<number>>(new Set());
  const [touchedValues, setTouchedValues] = React.useState<Set<number>>(new Set());

  const handleKeyValueChange = (index: number, oldKey: string, newKey: string, newValue: any) => {
    const newObj: Record<string, any> = {};
    
    // Check if newKey already exists in another entry (not counting empty keys)
    const isDuplicateKey = newKey !== "" && entries.some(([k], i) => {
      const displayK = k.startsWith('__empty_key_') ? '' : k;
      return i !== index && displayK === newKey;
    });
    
    // Rebuild object with all entries
    entries.forEach(([k, v], i) => {
      if (i === index) {
        // This is the entry being modified
        let keyToUse: string;
        
        if (newKey === "") {
          // Empty key - use temporary marker
          keyToUse = `__empty_key_${index}__`;
        } else if (isDuplicateKey) {
          // Duplicate key - use a marker to keep the entry visible with red border
          keyToUse = `__duplicate_${newKey}_${index}__`;
        } else {
          // Valid unique key
          keyToUse = newKey;
        }
        
        if (valueType === "integer" || valueType === "number") {
          newObj[keyToUse] = newValue ? Number(newValue) : "";
        } else {
          newObj[keyToUse] = newValue;
        }
      } else {
        // Keep other entries as-is
        newObj[k] = v;
      }
    });
    
    onChange(newObj);
  };

  const handleRemoveKey = (index: number) => {
    const newObj: Record<string, any> = {};
    entries.forEach(([k, v], i) => {
      if (i !== index) {
        newObj[k] = v;
      }
    });
    onChange(newObj);
  };

  const handleAddKey = () => {
    // Add entry with empty key using temporary marker
    const newIndex = entries.length;
    const tempKey = `__empty_key_${newIndex}__`;
    const newObj = { ...objValue, [tempKey]: valueType === "integer" || valueType === "number" ? "" : "" };
    onChange(newObj);
  };

  return (
    <div key={propName} className="space-y-2">
      {!skipLabel && (
        <>
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
          {propSchema.description && (
            <p className="text-xs text-gray-500 mt-1">{propSchema.description}</p>
          )}
        </>
      )}
      <div className="space-y-2 border rounded-lg p-3">
        {entries.map(([key, val], index) => {
          // Check if this is a temporary empty key marker
          const isEmptyKey = key.startsWith('__empty_key_');
          
          // Check if this is a duplicate key marker
          const isDuplicateMarker = key.startsWith('__duplicate_');
          let displayKey = key;
          
          if (isEmptyKey) {
            displayKey = '';
          } else if (isDuplicateMarker) {
            // Extract the actual key from __duplicate_keyname_index__
            const match = key.match(/^__duplicate_(.+)_\d+__$/);
            displayKey = match ? match[1] : key;
          }
          
          // Check if this key is duplicated (appears more than once)
          const allKeys = entries.map(([k]) => {
            if (k.startsWith('__empty_key_')) return '';
            if (k.startsWith('__duplicate_')) {
              const match = k.match(/^__duplicate_(.+)_\d+__$/);
              return match ? match[1] : k;
            }
            return k;
          });
          const keyCount = allKeys.filter(k => k === displayKey && k !== "").length;
          const isDuplicate = (displayKey !== "" && keyCount > 1) || isDuplicateMarker;
          
          // Check if key or value is empty
          const hasEmptyKey = displayKey === '' || isEmptyKey;
          const hasEmptyValue = val === '' || val === null || val === undefined || (typeof val === 'string' && val.trim() === '');
          
          // Only show empty validation if field has been touched (blurred)
          const showEmptyKeyError = hasEmptyKey && touchedKeys.has(index);
          const showEmptyValueError = hasEmptyValue && touchedValues.has(index);
          
          return (
          <div key={index} className="flex gap-2 items-center">
            <Input
              placeholder="key"
              value={displayKey}
              onChange={(e) => handleKeyValueChange(index, key, e.target.value, val)}
              onBlur={() => setTouchedKeys(prev => new Set(prev).add(index))}
              className={`flex-1 ${isDuplicate ? 'border-red-500 focus-visible:ring-red-500' : showEmptyKeyError ? 'border-orange-500 focus-visible:ring-orange-500' : ''}`}
              style={isDuplicate ? { boxShadow: '0 2px 8px rgba(239, 68, 68, 0.3)' } : showEmptyKeyError ? { boxShadow: '0 2px 8px rgba(249, 115, 22, 0.3)' } : undefined}
              title={isDuplicate ? 'Duplicate key name - please use a unique name' : showEmptyKeyError ? 'Key cannot be empty - this pair will not be submitted' : ''}
            />
            {valueType === "integer" || valueType === "number" ? (
              <Input
                type="number"
                placeholder="Value"
                value={typeof val === "number" ? val : val ? String(val) : ""}
                onChange={(e) => handleKeyValueChange(index, key, key, e.target.value)}
                onBlur={() => setTouchedValues(prev => new Set(prev).add(index))}
                className={`flex-1 ${showEmptyValueError ? 'border-orange-500 focus-visible:ring-orange-500' : ''}`}
                style={showEmptyValueError ? { boxShadow: '0 2px 8px rgba(249, 115, 22, 0.3)' } : undefined}
                title={showEmptyValueError ? 'Value cannot be empty - this pair will not be submitted' : ''}
              />
            ) : (
              <Input
                placeholder="Value"
                value={val ? String(val) : ""}
                onChange={(e) => handleKeyValueChange(index, key, key, e.target.value)}
                onBlur={() => setTouchedValues(prev => new Set(prev).add(index))}
                className={`flex-1 ${showEmptyValueError ? 'border-orange-500 focus-visible:ring-orange-500' : ''}`}
                style={showEmptyValueError ? { boxShadow: '0 2px 8px rgba(249, 115, 22, 0.3)' } : undefined}
                title={showEmptyValueError ? 'Value cannot be empty - this pair will not be submitted' : ''}
              />
            )}
            <Button
              type="button"
              variant="destructive"
              size="icon"
              className="h-8 w-8 flex-shrink-0"
              onClick={() => handleRemoveKey(index)}
            >
              <Minus className="h-4 w-4" />
            </Button>
          </div>
        );
        })}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAddKey}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Key-Value Pair
        </Button>
      </div>
    </div>
  );
}

// Render nested array of custom models (used within model properties)
function renderNestedCustomModelList(
  propName: string,
  propSchema: any,
  value: any[],
  onChange: (value: any[]) => void,
  required: boolean,
  defs?: Record<string, any>,
  skipLabel?: boolean
): React.ReactNode {
  const itemsSchema = propSchema.items;
  if (!itemsSchema) {
    return null;
  }

  // Check for $ref (reference to a model in $defs)
  let modelSchema: any = null;
  if (itemsSchema.$ref) {
    modelSchema = getModelSchemaFromRef(itemsSchema.$ref, defs || {});
  }
  // Check for inline object definition (type: "object" with properties)
  else if (itemsSchema.type === "object" && itemsSchema.properties) {
    modelSchema = itemsSchema;
  }

  if (!modelSchema || !modelSchema.properties) {
    return null;
  }

  const listValue = Array.isArray(value) ? value : [];
  const requiredProps = modelSchema.required || [];
  const properties = modelSchema.properties || {};

  // Create empty item based on schema
  const createEmptyItem = (): any => {
    const item: any = {};
    Object.keys(properties).forEach((propName) => {
      const propSchema = properties[propName];
      // Check if property is nullable
      const isNullable = propSchema.anyOf?.some((s: any) => s.type === "null");

      if (isNullable) {
        item[propName] = null;
      } else if (propSchema.type === "boolean") {
        item[propName] = false;
      } else if (propSchema.type === "number" || propSchema.type === "integer") {
        item[propName] = "";
      } else if (propSchema.type === "array") {
        item[propName] = [];
      } else if (propSchema.type === "object") {
        item[propName] = {};
      } else {
        item[propName] = "";
      }
    });
    return item;
  };

  return (
    <div key={propName} className="space-y-3">
      {!skipLabel && (
        <Label className="text-xs">
          {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
          {required && <span className="text-red-500 ml-1">*</span>}
        </Label>
      )}
      {listValue.map((item, index) => (
        <div key={index} className="p-3 border rounded-lg space-y-3 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">Item {index + 1}</Label>
            <Button
              type="button"
              variant="destructive"
              size="icon"
              className={`h-8 w-8 rounded-full flex-shrink-0 ${index === 0 && required ? 'invisible' : ''}`}
              onClick={() => {
                const newList = listValue.filter((_, i) => i !== index);
                onChange(newList);
              }}
            >
              <Minus className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-3">
            {Object.entries(properties).map(([nestedPropName, nestedPropSchema]: [string, any]) => {
              return renderModelProperty(
                nestedPropName,
                nestedPropSchema,
                item[nestedPropName],
                (newValue) => {
                  const newList = [...listValue];
                  newList[index] = {
                    ...newList[index],
                    [nestedPropName]: newValue,
                  };
                  onChange(newList);
                },
                requiredProps.includes(nestedPropName),
                defs
              );
            })}
          </div>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          onChange([...listValue, createEmptyItem()]);
        }}
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Item
      </Button>
    </div>
  );
}

// Render a single property of a custom model
function renderModelProperty(
  propName: string,
  propSchema: any,
  value: any,
  onChange: (value: any) => void,
  required: boolean,
  defs?: Record<string, any>
): React.ReactNode {
  const propType = propSchema.type;
  const isRequired = required;
  const placeholder = propSchema.description || `Enter ${propName}`;

  // Handle $ref (enum references)
  if (propSchema.$ref) {
    const enumValues = getEnumValuesFromRef(propSchema.$ref, defs || {});
    return (
      <div key={propName} className="space-y-2">
        <Label className="text-xs">
          {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
          {isRequired && <span className="text-red-500 ml-1">*</span>}
        </Label>
        <Select
          value={value || ""}
          onValueChange={onChange}
        >
          <SelectTrigger>
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent>
            {enumValues.map((enumValue: any) => (
              <SelectItem key={String(enumValue)} value={String(enumValue)}>
                {String(enumValue)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    );
  }

  // Handle nullable arrays (anyOf with null) - check this FIRST before propType
  if (propSchema.anyOf) {
    const arraySchema = propSchema.anyOf.find((s: any) => s.type === "array");
    const nullSchema = propSchema.anyOf.find((s: any) => s.type === "null");

    if (arraySchema && nullSchema) {
      const isNull = value === null || value === undefined;
      const arrayValue = isNull ? [] : (Array.isArray(value) ? value : []);

      // Check if the array schema has items.$ref pointing to an enum
      if (arraySchema.items?.$ref && isEnumRef(arraySchema.items.$ref, defs || {})) {
        const enumValues = getEnumValuesFromRef(arraySchema.items.$ref, defs || {});
        return (
          <div key={propName} className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs">
                {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                {isRequired && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <EnableCheckbox
                checked={!isNull}
                onChange={onChange}
                onEnable={() => []}
              />
            </div>
            {!isNull && (
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {enumValues.map((enumValue: any) => {
                    const isSelected = arrayValue.includes(enumValue);
                    return (
                      <Button
                        key={String(enumValue)}
                        type="button"
                        variant={isSelected ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          const newValues = isSelected
                            ? arrayValue.filter((v: any) => v !== enumValue)
                            : [...arrayValue, enumValue];
                          onChange(newValues.length > 0 ? newValues : null);
                        }}
                      >
                        {String(enumValue)}
                      </Button>
                    );
                  })}
                </div>
                {arrayValue.length > 0 && (
                  <div className="text-sm text-muted-foreground">
                    Selected: {arrayValue.join(", ")}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      }

      // Check if the array schema has items.$ref or inline object definition (custom model array)
      if (arraySchema.items?.$ref || (arraySchema.items?.type === "object" && arraySchema.items?.properties)) {
        return (
          <div key={propName} className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs">
                {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                {isRequired && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <EnableCheckbox
                checked={!isNull}
                onChange={onChange}
                onEnable={() => []}
              />
            </div>
            {!isNull && renderNestedCustomModelList(
              propName,
              arraySchema,
              arrayValue,
              onChange,
              isRequired,
              defs,
              true // skipLabel since we already have a label above
            )}
          </div>
        );
      }

      // Handle nullable array of primitives (like Array<string> | null)
      return (
        <div key={propName} className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">
              {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
              {isRequired && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <EnableCheckbox
              checked={!isNull}
              onChange={onChange}
              onEnable={() => []}
            />
          </div>
          {!isNull && (
            <div className="space-y-2">
              {arrayValue.map((item: any, index: number) => (
                <div key={index} className="flex gap-2 items-center">
                  <Input
                    placeholder={`Item ${index + 1}`}
                    value={item || ""}
                    onChange={(e) => {
                      const newList = [...arrayValue];
                      newList[index] = e.target.value;
                      onChange(newList);
                    }}
                    className="flex-1"
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="icon"
                    className="h-8 w-8 flex-shrink-0"
                    onClick={() => {
                      const newList = arrayValue.filter((_: any, i: number) => i !== index);
                      onChange(newList.length > 0 ? newList : null);
                    }}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  onChange([...arrayValue, ""]);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Item
              </Button>
            </div>
          )}
        </div>
      );
    }
  }

  // Handle nullable objects with dynamic properties (object with additionalProperties | null)
  if (propSchema.anyOf) {
    const objectSchema = propSchema.anyOf.find((s: any) =>
      s.type === "object" && s.additionalProperties !== undefined && s.additionalProperties !== false
    );
    const nullSchema = propSchema.anyOf.find((s: any) => s.type === "null");

    if (objectSchema && nullSchema) {
      const isNull = value === null || value === undefined;
      return (
        <div key={propName} className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">
              {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
              {isRequired && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <EnableCheckbox
              checked={!isNull}
              onChange={onChange}
              onEnable={() => ({})}
            />
          </div>
          {!isNull && renderDynamicObject(
            propName,
            objectSchema,
            value || {},
            onChange,
            isRequired,
            defs,
            true // skipLabel since we already have a label above
          )}
        </div>
      );
    }
  }

  // Handle nullable primitives (string | null, integer | null, etc.)
  if (propSchema.anyOf) {
    const primitiveSchema = propSchema.anyOf.find((s: any) =>
      s.type === "string" || s.type === "integer" || s.type === "number"
    );
    const nullSchema = propSchema.anyOf.find((s: any) => s.type === "null");

    if (primitiveSchema && nullSchema) {
      const isNull = value === null || value === undefined;
      const primitiveType = primitiveSchema.type;

      return (
        <div key={propName} className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">
              {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
              {isRequired && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <EnableCheckbox
              checked={!isNull}
              onChange={onChange}
              onEnable={() => ""}
            />
          </div>
          {!isNull && (
            primitiveType === "integer" || primitiveType === "number" ? (
              <Input
                type="number"
                placeholder={placeholder}
                value={value || ""}
                onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
              />
            ) : (
              <Input
                placeholder={placeholder}
                value={value || ""}
                onChange={(e) => onChange(e.target.value)}
              />
            )
          )}
        </div>
      );
    }
  }

  // Handle different property types
  switch (propType) {
    case "array":
      // Check if array items reference an enum (for non-nullable arrays)
      if (propSchema.items?.$ref && isEnumRef(propSchema.items.$ref, defs || {})) {
        const enumValues = getEnumValuesFromRef(propSchema.items.$ref, defs || {});
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div key={propName} className="space-y-2">
            <Label className="text-xs">
              {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
              {isRequired && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <div className="flex flex-wrap gap-2">
              {enumValues.map((enumValue: any) => {
                const isSelected = selectedValues.includes(enumValue);
                return (
                  <Button
                    key={String(enumValue)}
                    type="button"
                    variant={isSelected ? "default" : "outline"}
                    size="sm"
                    onClick={() => {
                      const newValues = isSelected
                        ? selectedValues.filter((v: any) => v !== enumValue)
                        : [...selectedValues, enumValue];
                      onChange(newValues);
                    }}
                  >
                    {String(enumValue)}
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

      // Check if array items reference a custom model or have inline object definition (for non-nullable arrays)
      if (propSchema.items?.$ref || (propSchema.items?.type === "object" && propSchema.items?.properties)) {
        return renderNestedCustomModelList(
          propName,
          propSchema,
          Array.isArray(value) ? value : [],
          onChange,
          isRequired,
          defs
        );
      }

      // Handle regular arrays of primitives
      const arrayValue = Array.isArray(value) ? value : [];
      return (
        <div key={propName} className="space-y-2">
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
          {arrayValue.map((item: any, index: number) => (
            <div key={index} className="flex gap-2 items-center">
              <Input
                placeholder={`Item ${index + 1}`}
                value={item || ""}
                onChange={(e) => {
                  const newList = [...arrayValue];
                  newList[index] = e.target.value;
                  onChange(newList);
                }}
                className="flex-1"
              />
              <Button
                type="button"
                variant="destructive"
                size="icon"
                className={`h-8 w-8 flex-shrink-0 ${index === 0 && isRequired ? 'invisible' : ''}`}
                onClick={() => {
                  const newList = arrayValue.filter((_: any, i: number) => i !== index);
                  onChange(newList);
                }}
              >
                <Minus className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              onChange([...arrayValue, ""]);
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Item
          </Button>
        </div>
      );
    case "string":
      return (
        <div key={propName} className="space-y-2">
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Textarea
            placeholder={placeholder}
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            rows={3}
            className="resize-y"
          />
        </div>
      );
    case "integer":
    case "number":
      return (
        <div key={propName} className="space-y-2">
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Input
            type="number"
            placeholder={placeholder}
            value={value || ""}
            onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
          />
        </div>
      );
    case "boolean":
      return (
        <div key={propName} className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => onChange(e.target.checked)}
            className="h-4 w-4"
          />
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
        </div>
      );
    case "object":
      // Check if object has additionalProperties (dynamic keys)
      if (propSchema.additionalProperties !== undefined && propSchema.additionalProperties !== false) {
        return renderDynamicObject(
          propName,
          propSchema,
          value,
          onChange,
          isRequired,
          defs
        );
      }

      // For nested objects without dynamic properties, render as JSON textarea
      return (
        <div key={propName} className="space-y-2">
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Textarea
            placeholder="Enter JSON object"
            value={typeof value === "string" ? value : JSON.stringify(value || {}, null, 2)}
            onChange={(e) => {
              try {
                onChange(JSON.parse(e.target.value));
              } catch {
                onChange(e.target.value);
              }
            }}
            rows={4}
            className="resize-y font-mono text-sm"
          />
        </div>
      );
    default:
      return (
        <div key={propName} className="space-y-2">
          <Label className="text-xs">
            {propName.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            {isRequired && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Textarea
            placeholder={placeholder}
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            rows={3}
            className="resize-y"
          />
        </div>
      );
  }
}

// Render a custom model field (single)
function renderCustomModelField(
  field: RequiredInputField,
  typeInfo: TypeInfo,
  value: any,
  onFormChange: (fieldName: string, value: any) => void
): React.ReactNode {
  const modelSchema = typeInfo.model_schema;
  if (!modelSchema || !modelSchema.properties) {
    return null;
  }

  const currentValue = value || {};
  const requiredProps = modelSchema.required || [];
  const defs = modelSchema.$defs || {};
  const properties = modelSchema.properties || {};

  return (
    <div key={field.field_name} className="space-y-4 p-4 border rounded-lg">
      <Label className="text-base font-semibold">
        {formatFieldName(field.field_name)}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      <div className="space-y-3">
        {Object.entries(properties).map(([propName, propSchema]: [string, any]) => {
          return renderModelProperty(
            propName,
            propSchema,
            currentValue[propName],
            (newValue) => {
              onFormChange(field.field_name, {
                ...currentValue,
                [propName]: newValue,
              });
            },
            requiredProps.includes(propName),
            defs
          );
        })}
      </div>
    </div>
  );
}

// Render a list of custom models
function renderCustomModelListField(
  field: RequiredInputField,
  typeInfo: TypeInfo,
  value: any[],
  onFormChange: (fieldName: string, value: any[]) => void
): React.ReactNode {
  const modelSchema = typeInfo.model_schema;
  if (!modelSchema || !modelSchema.properties) {
    return null;
  }

  const listValue = value || [];
  const requiredProps = modelSchema.required || [];
  const defs = modelSchema.$defs || {};
  const properties = modelSchema.properties || {};

  // Create empty item based on schema
  const createEmptyItem = (): any => {
    const item: any = {};
    Object.keys(properties).forEach((propName) => {
      const propSchema = properties[propName];
      // Check if property is nullable
      const isNullable = propSchema.anyOf?.some((s: any) => s.type === "null");

      if (isNullable) {
        item[propName] = null;
      } else if (propSchema.type === "boolean") {
        item[propName] = false;
      } else if (propSchema.type === "number" || propSchema.type === "integer") {
        item[propName] = "";
      } else {
        item[propName] = "";
      }
    });
    return item;
  };

  return (
    <div key={field.field_name} className="space-y-3">
      <Label className="text-base font-semibold">
        {formatFieldName(field.field_name)}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {listValue.map((item, index) => (
        <div key={index} className="p-4 border rounded-lg space-y-3">
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">Item {index + 1}</Label>
            <Button
              type="button"
              variant="destructive"
              size="icon"
              className={`h-8 w-8 rounded-full flex-shrink-0 ${index === 0 ? 'invisible' : ''}`}
              onClick={() => {
                const newList = listValue.filter((_, i) => i !== index);
                onFormChange(field.field_name, newList);
              }}
            >
              <Minus className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-3">
            {Object.entries(properties).map(([propName, propSchema]: [string, any]) => {
              return renderModelProperty(
                propName,
                propSchema,
                item[propName],
                (newValue) => {
                  const newList = [...listValue];
                  newList[index] = {
                    ...newList[index],
                    [propName]: newValue,
                  };
                  onFormChange(field.field_name, newList);
                },
                requiredProps.includes(propName),
                defs
              );
            })}
          </div>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          onFormChange(field.field_name, [...listValue, createEmptyItem()]);
        }}
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Row
      </Button>
    </div>
  );
}

// Render basic field types
function renderBasicField(
  field: RequiredInputField,
  typeInfo: TypeInfo,
  value: any,
  onFormChange: (fieldName: string, value: any) => void
): React.ReactNode {
  const fieldType = typeInfo.type;
  const placeholder = field.placeholder || `Enter ${field.field_name}`;

  switch (fieldType) {
    case "date":
      return (
        <div key={field.field_name} className="space-y-2">
          <Label>
            {formatFieldName(field.field_name)}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={`w-full justify-start text-left font-normal ${!value && "text-muted-foreground"
                  }`}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {value ? (
                  format(new Date(value), "PPP")
                ) : (
                  <span>Select date</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={value ? new Date(value) : undefined}
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
    case "int":
    case "integer":
    case "float":
    case "number":
      return (
        <div key={field.field_name} className="space-y-2">
          <Label>
            {formatFieldName(field.field_name)}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Input
            type="number"
            placeholder={placeholder}
            value={value || ""}
            onChange={(e) => onFormChange(field.field_name, e.target.value ? Number(e.target.value) : "")}
          />
        </div>
      );
    case "bool":
    case "boolean":
      return (
        <div key={field.field_name} className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => onFormChange(field.field_name, e.target.checked)}
            className="h-4 w-4"
          />
          <Label>
            {formatFieldName(field.field_name)}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
        </div>
      );
    case "string":
    default:
      return (
        <div key={field.field_name} className="space-y-2">
          <Label>
            {formatFieldName(field.field_name)}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Textarea
            placeholder={placeholder}
            value={value || ""}
            onChange={(e) => onFormChange(field.field_name, e.target.value)}
            rows={3}
          />
        </div>
      );
  }
}

// Render enum field (single or list)
function renderEnumField(
  field: RequiredInputField,
  typeInfo: TypeInfo,
  value: any,
  onFormChange: (fieldName: string, value: any) => void
): React.ReactNode {
  const enumValues = typeInfo.enum_values || [];
  const isList = typeInfo.is_list;

  if (isList) {
    const selectedValues = Array.isArray(value) ? value : [];
    return (
      <div key={field.field_name} className="space-y-2">
        <Label>
          {field.field_name === "templateId"
            ? "Template Id"
            : formatFieldName(field.field_name)}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </Label>
        <div className="flex flex-wrap gap-2">
          {enumValues.map((enumValue: any) => {
            const isSelected = selectedValues.includes(enumValue);
            return (
              <Button
                key={String(enumValue)}
                type="button"
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  const newValues = isSelected
                    ? selectedValues.filter((v: any) => v !== enumValue)
                    : [...selectedValues, enumValue];
                  onFormChange(field.field_name, newValues);
                }}
              >
                {String(enumValue)}
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

  // Single enum
  return (
    <div key={field.field_name} className="space-y-2">
      <Label>
        {formatFieldName(field.field_name)}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      <Select
        value={value ? String(value) : ""}
        onValueChange={(val) => onFormChange(field.field_name, val)}
      >
        <SelectTrigger>
          <SelectValue placeholder={field.placeholder || `Select ${field.field_name}`} />
        </SelectTrigger>
        <SelectContent>
          {enumValues.map((enumValue: any) => (
            <SelectItem key={String(enumValue)} value={String(enumValue)}>
              {String(enumValue)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function KickoffForm({
  requiredInputs,
  dynamicFormData,
  onFormChange,
  onSubmit,
}: KickoffFormProps) {
  const renderField = (field: RequiredInputField): React.ReactNode => {
    const typeInfo = field.type_info as TypeInfo;
    const value = dynamicFormData[field.field_name];

    // Field type detection order:
    // 1. Check if it's a list
    if (typeInfo.is_list) {
      // List of custom models
      if (typeInfo.is_custom_model && typeInfo.model_schema) {
        return renderCustomModelListField(field, typeInfo, value || [], onFormChange);
      }
      // List of enums (already handled above, but enum check comes first)
      if (typeInfo.is_enum && typeInfo.enum_values) {
        return renderEnumField(field, typeInfo, value, onFormChange);
      }
      // List of primitives - render as repeatable inputs
      return (
        <div key={field.field_name} className="space-y-2">
          <Label>
            {formatFieldName(field.field_name)}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          {(value || []).map((item: any, index: number) => (
            <div key={index} className="flex gap-2 items-center">
              <Input
                placeholder={field.placeholder || `Item ${index + 1}`}
                value={item || ""}
                onChange={(e) => {
                  const newList = [...(value || [])];
                  newList[index] = e.target.value;
                  onFormChange(field.field_name, newList);
                }}
                className="flex-1"
              />
              <Button
                type="button"
                variant="destructive"
                size="icon"
                className={`h-8 w-8 ${index === 0 ? 'invisible' : ''}`}
                onClick={() => {
                  const newList = (value || []).filter((_: any, i: number) => i !== index);
                  onFormChange(field.field_name, newList);
                }}
              >
                <Minus className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              onFormChange(field.field_name, [...(value || []), ""]);
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Item
          </Button>
        </div>
      );
    }

    // 2. Check if it's an enum
    if (typeInfo.is_enum && typeInfo.enum_values) {
      return renderEnumField(field, typeInfo, value, onFormChange);
    }

    // 3. Check if it's a custom model
    if (typeInfo.is_custom_model && typeInfo.model_schema) {
      return renderCustomModelField(field, typeInfo, value, onFormChange);
    }

    // 4. Handle basic types
    return renderBasicField(field, typeInfo, value, onFormChange);
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      onSubmit(e);
    }} className="space-y-4">
      {requiredInputs.map((field) => renderField(field))}
    </form>
  );
}
